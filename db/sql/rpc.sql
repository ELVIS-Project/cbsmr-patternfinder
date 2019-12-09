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
    INSERT INTO Note(pid, n, nid) SELECT NEW.pid, n, nid FROM generate_notes(NEW.music21_xml);

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
