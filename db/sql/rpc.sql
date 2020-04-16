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
    DELETE FROM Note WHERE pid=NEW.pid;
    INSERT INTO Note(pid, n, nid, part_id) SELECT NEW.pid, n, nid, part_id FROM generate_notes(NEW.music21_xml);

    DELETE FROM MeasureOnsetMap WHERE pid=NEW.pid;
    INSERT INTO MeasureOnsetMap(pid, mid, onset) SELECT NEW.pid, mid, onset FROM smrpy_measure_onset_map(NEW.music21_xml);

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER index_piece_after_insert AFTER INSERT OR UPDATE OF symbolic_data ON Piece FOR EACH ROW EXECUTE PROCEDURE index_piece_after_insert();

CREATE OR REPLACE FUNCTION symbolic_data_to_m21_xml(symbolic_data TEXT) RETURNS TEXT AS $$
    from plpyext import symbolic_data_to_m21_xml
    return symbolic_data_to_m21_xml(symbolic_data)
$$ LANGUAGE plpython3u IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION smrpy_excerpt(m21_xml TEXT, nids INTEGER[], measure_start INTEGER, measure_end INTEGER, color TEXT) RETURNS TEXT AS $$
    from plpyext import excerpt
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
    from plpyext import generate_notes
    return generate_notes(symbolic_data)
$$ LANGUAGE plpython3u IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION smrpy_measure_onset_map(symbolic_data TEXT) RETURNS SETOF MeasureOnsetMap AS $$
    from plpyext import measure_onset_map
    return measure_onset_map(symbolic_data)
$$ LANGUAGE plpython3u IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION smrpy_search(p_nids INTEGER[], t_nids INTEGER[], len_pattern INTEGER, threshold INTEGER) RETURNS TABLE(nids INTEGER[]) AS $$
    from plpyext import lemstrom_search
    return lemstrom_search.search(p_nids, t_nids, len_pattern, threshold)
$$ LANGUAGE plpython3u;

CREATE OR REPLACE VIEW search AS
	WITH vecs AS (
		SELECT
            EnumeratedNoteVector.pid,
			array_agg(ARRAY[query.l_nid, query.r_nid] ORDER BY EnumeratedNoteVector.r_nid) AS p_nids,
			array_agg(ARRAY[EnumeratedNoteVector.l_nid, EnumeratedNoteVector.r_nid] ORDER BY EnumeratedNoteVector.r_nid) AS t_nids
		FROM index_query('{"(0.0, 67)", "(0.5, 70)", "(1.0, 69)", "(1.5, 62)", "(2.0, 69)", "(3.0, 67)"}', 2) AS query
		JOIN EnumeratedNoteVector
		ON query.y = EnumeratedNoteVector.y AND ((EnumeratedNoteVector.x > 0 AND query.x > 0) OR (EnumeratedNoteVector.x = 0 AND query.x = 0))
		WHERE EnumeratedNoteVector.w < 3
		GROUP BY EnumeratedNoteVector.pid
	)

	SELECT smrpy_search(vecs.p_nids, vecs.t_nids, 6, 5) FROM vecs WHERE pid=0;

CREATE OR REPLACE FUNCTION smrpy_search(pids INTEGER[], p_binds INTEGER[][], t_binds INTEGER[][], p_vecs INTEGER[][], t_vecs INTEGER[][]) RETURNS TABLE(pid INTEGER, nids INTEGER[]) AS $$
    from plpyext import search
    search(pids, p_binds, t_binds, p_vecs, t_vecs)
$$ LANGUAGE plpython3u;

CREATE OR REPLACE FUNCTION search_sql_two(query POINT[], target_window INTEGER, within_part BOOLEAN) RETURNS TABLE(pid INTEGER, nids INTEGER[]) AS $$
WITH RECURSIVE
vecs AS (
    SELECT
        EnumeratedNoteVector.pid,
        ARRAY[query.l[0], query.l[1], query.r[0], query.r[1]] AS p_notes,
        ARRAY[EnumeratedNoteVector.l[0], EnumeratedNoteVector.l[1], EnumeratedNoteVector.r[0], EnumeratedNoteVector.r[1]] AS t_notes,
        ARRAY[EnumeratedNoteVector.l_nid, EnumeratedNoteVector.r_nid] AS t_nids
    FROM EnumeratedNoteVector
    JOIN index_query(query, 1) query
    ON query.y = EnumeratedNoteVector.y
    WHERE ((EnumeratedNoteVector.x > 0 AND query.x > 0) OR (EnumeratedNoteVector.x = 0 AND query.x = 0))
    AND EnumeratedNoteVector.w <= target_window
	AND (
        (EnumeratedNoteVector.within_part AND search_sql_two.within_part)
        OR (NOT search_sql_two.within_part)
    )
),
extension AS (SELECT
    pid,
    vecs.p_notes[1:2] AS p_bind,
    vecs.t_notes[1:2] AS t_bind,
    MIN(p_notes ORDER BY t_notes ASC) AS p_notes,
    MIN(t_notes ORDER BY t_notes ASC) AS t_notes,
    MIN(t_nids ORDER BY t_notes ASC) AS t_nids
FROM vecs
GROUP BY (pid, p_notes[1:2], t_notes[1:2])
)
, k_tables(pid, last_p, t_notes, t_nids, t_intervening_count) AS (
        SELECT      
            pid,
            p_notes[3:4],
            t_notes,
            t_nids,
            t_nids[2] - t_nids[1]
        FROM vecs
        UNION
            SELECT
                ext.pid,
                ext.p_notes[3:4],
                k_tables.t_notes || ext.t_notes[3:4],
                k_tables.t_nids || ext.t_nids[2:2],
                k_tables.t_intervening_count + (ext.t_nids[2] - ext.t_nids[1])
            FROM k_tables JOIN extension ext
            ON k_tables.pid = ext.pid
            AND k_tables.last_p = ext.p_notes[1:2]
            AND k_tables.t_notes[array_length(k_tables.t_notes, 1) - 1 : array_length(k_tables.t_notes, 1)] = ext.t_notes[1:2]
            --AND k_tables.t_intervening_count + ext.t_nids[2] - ext.t_nids[1] <= 5
    )
SELECT pid, t_nids FROM k_tables;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION search_sql(query POINT[]) RETURNS TABLE(pid INTEGER, nids INTEGER[]) AS $$
WITH RECURSIVE
vecs AS (
    SELECT    
        EnumeratedNoteVector.pid,  
        ARRAY[query.l_nid, query.r_nid] AS p_nids,
        ARRAY[EnumeratedNoteVector.l_nid, EnumeratedNoteVector.r_nid] AS t_nids
    FROM EnumeratedNoteVector
    JOIN index_query(query, 1) query
    ON query.y = EnumeratedNoteVector.y
    AND ((EnumeratedNoteVector.x > 0 AND query.x > 0) OR (EnumeratedNoteVector.x = 0 AND query.x = 0))
    WHERE EnumeratedNoteVector.w <= 3
),
postcedent AS (
    SELECT
        pid,
        MIN(t_nids) AS t_nids,
        MIN(p_nids[1] ORDER BY t_nids) AS p_bind
    FROM vecs
    GROUP BY pid, t_nids[1]
),
antecedent AS (
    SELECT
        pid,
        MIN(t_nids) AS t_nids,
        MIN(p_nids[2] ORDER BY t_nids) AS p_bind
    FROM vecs
    GROUP BY pid, t_nids[2]
),
chains(pid, last_p, t_nids) AS (
        SELECT
            pid,
            p_nids[2] AS last_p,
            t_nids
        FROM vecs
        UNION
            SELECT
                chains.pid,
                vecs.p_nids[1],
                chains.t_nids || vecs.t_nids[2]
            FROM chains JOIN vecs
            ON chains.pid = vecs.pid
            AND chains.last_p = vecs.p_nids[1]
            AND chains.t_nids[array_length(chains.t_nids, 1)] = vecs.t_nids[1]
)
SELECT DISTINCT ON (t_nids[1]) pid, t_nids FROM chains;
$$ LANGUAGE SQL IMMUTABLE STRICT;

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

CREATE OR REPLACE FUNCTION index_query(query POINT[], window_size INTEGER) RETURNS SETOF EnumeratedNoteVector AS $$
SELECT 
    -1,
	(q2.n - q1.n)[0]::NUMERIC AS x,
	(q2.n - q1.n)[1]::INTEGER AS y,
    q1.n,
    q2.n,
    q1.nid::INTEGER AS l_nid,
    q2.nid::INTEGER AS r_nid,
    'query',
    'query',
    TRUE,
    (q2.nid - q1.nid)::INTEGER AS w
FROM (SELECT unnest AS n, ordinality AS nid FROM unnest(query) WITH ORDINALITY) q1
JOIN (SELECT unnest AS n, ordinality AS nid FROM unnest(query) WITH ORDINALITY) q2
ON q2.nid > q1.nid
AND q2.nid - q1.nid <= window_size
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION index_piece_notevectors_sql(pid INTEGER, window_size INTEGER) RETURNS SETOF EnumeratedNoteVector AS $$
BEGIN
    DELETE FROM EnumeratedNoteVector WHERE enumeratednotevector.pid=index_piece_notevectors_sql.pid;
	RETURN QUERY
    WITH notes AS (
		SELECT * FROM Note WHERE index_piece_notevectors_sql.pid = Note.pid
	),
	vecs AS (
		SELECT
			index_piece_notevectors_sql.pid,
			(n2.n - n1.n)[0] AS x,
			(n2.n - n1.n)[1] AS y,
			n1.n,
			n2.n,
			n1.nid,
			n2.nid,
			n1.part_id,
			n2.part_id,
			n1.part_id = n2.part_id AS within_part,
            n2.nid - n1.nid AS w
		FROM notes n1 JOIN notes n2
		ON n2.nid > n1.nid
		AND n2.nid - n1.nid <= window_size
	)
	INSERT INTO EnumeratedNoteVector(pid, x, y, l, r, l_nid, r_nid, l_part_id, r_part_id, within_part, w) (SELECT * FROM vecs)
    RETURNING *;
END;
$$ LANGUAGE plpgsql;

