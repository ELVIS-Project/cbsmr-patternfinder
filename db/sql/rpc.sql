CREATE EXTENSION plpython3u;

CREATE OR REPLACE FUNCTION index_piece() RETURNS TRIGGER AS $$
BEGIN
    NEW.music21_xml = symbolic_data_to_m21_xml(NEW.symbolic_data);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER index_piece_before_insert BEFORE INSERT OR UPDATE OF symbolic_data ON Piece FOR EACH ROW EXECUTE PROCEDURE index_piece();

CREATE OR REPLACE FUNCTION index_piece_after_insert() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO Note(pid, n, nid) SELECT NEW.pid, n, nid FROM generate_notes(NEW.music21_xml);
    PERFORM index_piece_notewindows(NEW.pid, 40);
    INSERT INTO MeasureOnsetMap(pid, mid, onset) SELECT NEW.pid, mid, onset FROM smrpy_measure_onset_map(NEW.music21_xml);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER index_piece_after_insert AFTER INSERT OR UPDATE OF symbolic_data ON Piece FOR EACH ROW EXECUTE PROCEDURE index_piece_after_insert();

CREATE OR REPLACE FUNCTION symbolic_data_to_m21_xml(symbolic_data TEXT) RETURNS TEXT AS $$
    from smrpy import symbolic_data_to_m21_xml
    return symbolic_data_to_m21_xml(symbolic_data)
$$ LANGUAGE plpython3u IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION smrpy_excerpt(m21_xml TEXT, nids INTEGER[], measure_start INTEGER, measure_end INTEGER, color TEXT) RETURNS TEXT AS $$
    from smrpy import excerpt
    return excerpt(m21_xml, nids, measure_start, measure_end, color)
$$ LANGUAGE plpython3u IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION colored_excerpt(pid INTEGER, nids INTEGER[], color TEXT) RETURNS TEXT AS $$
	WITH offsets AS (
		SELECT MAX(Note.n[0]), MIN(Note.n[0]) FROM unnest(nids) JOIN Note ON (Note.nid, Note.pid) = (unnest, colored_excerpt.pid)
	),
	mids AS (
		SELECT 
			(SELECT COALESCE(MAX(mid), 1) AS measure_start FROM MeasureOnsetMap WHERE onset <= (SELECT min FROM offsets) AND MeasureOnsetMap.pid=colored_excerpt.pid),
			(SELECT COALESCE(MIN(mid), -1) AS measure_end FROM MeasureOnsetMap WHERE onset >= (SELECT max FROM offsets) AND MeasureOnsetMap.pid=colored_excerpt.pid)
	)
    SELECT smrpy_excerpt(Piece.music21_xml, nids, (SELECT measure_start FROM mids), (SELECT measure_end FROM mids), color) FROM Piece WHERE colored_excerpt.pid = Piece.pid;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION generate_notes(symbolic_data TEXT) RETURNS SETOF Note AS $$
    from smrpy import generate_notes
    return generate_notes(symbolic_data)
$$ LANGUAGE plpython3u IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION smrpy_measure_onset_map(symbolic_data TEXT) RETURNS SETOF MeasureOnsetMap AS $$
    from smrpy import measure_onset_map
    return measure_onset_map(symbolic_data)
$$ LANGUAGE plpython3u IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION index_piece_notewindows(pid INTEGER, window_size INTEGER) RETURNS VOID AS $$
DECLARE
    notes POINT[];
BEGIN
    SELECT array_agg(Note.n ORDER BY (Note.n[0], Note.n[1])) INTO notes FROM Note WHERE Note.pid=index_piece_notewindows.pid;
    DELETE FROM NoteWindow WHERE NoteWindow.pid=index_piece_notewindows.pid;
    INSERT INTO NoteWindow(pid, u, v, note_ids, onset_start, onset_end, unnormalized, normalized)
        SELECT index_piece_notewindows.pid, u, v, note_ids, onset_start, onset_end, unnormalized, normalized FROM smrpy_generate_notewindows(notes, window_size);
    UPDATE Piece SET window_size = index_piece_notewindows.window_size WHERE Piece.pid = index_piece_notewindows.pid;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION index_piece_notevectors(pid INTEGER) RETURNS VOID AS $$
DECLARE
    notes POINT[];
BEGIN
    SELECT array_agg(Note.n ORDER BY (Note.n[0], Note.n[1])) INTO notes FROM Note WHERE Note.pid=index_piece_notevectors.pid;
    DELETE FROM NoteVector WHERE NoteVector.pid=index_piece_notevectors.pid;
    INSERT INTO NoteVector(pid, x, y, l, r)
        SELECT index_piece_notevectors.pid, x, y, l, r FROM smrpy_generate_notevectors(notes);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION smrpy_generate_notewindows(notes POINT[], window_size INTEGER) RETURNS TABLE(like NoteWindow) AS $$
    from smrpy import generate_notewindows
    return generate_notewindows(notes, window_size)
$$ LANGUAGE plpython3u IMMUTABLE STRICT;


CREATE OR REPLACE FUNCTION search_sql_gin_exact(normalized_query POINT[]) RETURNS TABLE(pid INTEGER, notes POINT[], nids INTEGER[]) AS
$$
WITH matching_windows AS (
        SELECT pid, u, v, normalized, unnormalized, note_ids
        FROM notewindow
        WHERE (normalized @> normalized_query)),
    window_note_matches AS (
        SELECT w.pid, u, v, w.unnormalized[array_position(w.normalized, pattern_notes.n)] AS note,  w.note_ids[array_position(w.normalized, pattern_notes.n)] AS nid
        FROM (SELECT unnest(normalized_query) AS n) AS pattern_notes JOIN matching_windows AS w
        ON true)
SELECT window_note_matches.pid, array_agg(note) notes, array_agg(nid) nids
FROM window_note_matches
GROUP BY (window_note_matches.pid, u, v);
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION smrpy_search_filtered(query POINT[], transpositions INTEGER[], intervening INTEGER[], inexact INTEGER[]) RETURNS TABLE(pid INTEGER, nids INTEGER[], notes POINT[]) AS $$
    from smrpy import search_filtered
    return search_filtered(query, transpositions, intervening, inexact)
$$ LANGUAGE plpython3u IMMUTABLE STRICT;
	
CREATE OR REPLACE FUNCTION smrpy_search(query POINT[]) RETURNS TABLE(pid INTEGER, nids INTEGER[], notes POINT[]) AS $$
    from smrpy import search
    return search(query)
$$ LANGUAGE plpython3u IMMUTABLE STRICT;
	
CREATE OR REPLACE FUNCTION search(query POINT[]) RETURNS TABLE(pid INTEGER, name TEXT, nids INTEGER[], notes POINT[]) AS $$
    SELECT
        Piece.pid,
        Piece.name,
        smrpy_search.nids,
        smrpy_search.notes
        FROM smrpy_search(query)
        JOIN Piece ON smrpy_search.pid = Piece.pid;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION search_filtered(query POINT[], transpositions INTEGER[], intervening INTEGER[], inexact INTEGER[]) RETURNS TABLE(pid INTEGER, name TEXT, nids INTEGER[], notes POINT[]) AS $$
    SELECT
        Piece.pid,
        Piece.name,
        smrpy_search_filtered.nids,
        smrpy_search_filtered.notes
        FROM smrpy_search_filtered(query, transpositions, intervening, inexact)
        JOIN Piece ON smrpy_search_filtered.pid = Piece.pid;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION smrpy_generate_notevectors(points POINT[]) RETURNS TABLE(x NUMERIC, y INTEGER, l POINT, r POINT) AS $$
    from smrpy import generate_notevectors
    return generate_notevectors(points)
$$ LANGUAGE plpython3u IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION index_piece_notevectors_sql(pid INTEGER, window_size INTEGER) RETURNS VOID AS $$
WITH notes AS (
	SELECT pid, n, nid FROM Note WHERE index_piece_notevectors_sql.pid = Note.pid
),
vecs AS (
	SELECT
		index_piece_notevectors_sql.pid,
		(n2.n - n1.n)[0] AS x,
		(n2.n - n1.n)[1] AS y,
		n1.n,
		n2.n,
		n1.nid,
		n2.nid
	FROM notes n1 JOIN notes n2
	ON n2.nid > n1.nid
	AND n2.nid - n1.nid < window_size
	AND n2.pid = n1.pid
)
INSERT INTO EnumeratedNoteVector(pid, x, y, l, r, l_nid, r_nid) (SELECT * FROM vecs)
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION search_lemstrom(query POINT[]) RETURNS TABLE(pid INTEGER, notes DOUBLE PRECISION[]) AS $$
WITH RECURSIVE
query AS (
    SELECT * FROM smrpy_generate_notevectors('{"(0.0, 67)","(0.5, 70)","(1.0, 69)","(1.5, 62)","(2.0, 69)","(3.0, 67)"}'::POINT[])
),
vecs AS (
    SELECT
        pid,
        ARRAY[query.l[0], query.l[1], query.r[0], query.r[1]] AS p_notes,
        ARRAY[EnumeratedNoteVector.l[0], EnumeratedNoteVector.l[1], EnumeratedNoteVector.r[0], EnumeratedNoteVector.r[1]] AS t_notes
    FROM EnumeratedNoteVector
    JOIN query
    ON query.y = EnumeratedNoteVector.y
    AND EnumeratedNoteVector.x > 0
    AND EnumeratedNoteVector.x < 2.5
    AND (query.x = 0.5 OR query.l[0]=2)
), k_tables(pid, last_p, t_notes) AS (
        SELECT
            pid,
            p_notes[3:4],
            t_notes
        FROM vecs
        UNION
            SELECT
                vecs.pid,
                vecs.p_notes[3:4],
                k_tables.t_notes || vecs.t_notes[3:4]
            FROM k_tables JOIN vecs
            ON k_tables.pid = vecs.pid
            AND k_tables.last_p = vecs.p_notes[1:2]
            AND k_tables.t_notes[array_length(k_tables.t_notes, 1) - 1 : array_length(k_tables.t_notes, 1)] = vecs.t_notes[1:2]
    )
SELECT pid, t_notes FROM k_tables WHERE array_length(t_notes, 1) = 12;
$$ LANGUAGE SQL;
