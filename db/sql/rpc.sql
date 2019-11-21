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
    INSERT INTO MeasureOnsetMap(pid, mid, onset) SELECT NEW.pid, mid, onset FROM smrpy_measure_onset_map(NEW.music21_xml);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER index_piece_after_insert AFTER INSERT OR UPDATE OF symbolic_data ON Piece FOR EACH ROW EXECUTE PROCEDURE index_piece_after_insert();

CREATE OR REPLACE FUNCTION smrpy_excerpt(pid INTEGER, nids INTEGER[]) RETURNS TEXT AS $$
    from smrpy import excerpt
    return excerpt(pid, nids)
$$ LANGUAGE plpython3u IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION symbolic_data_to_m21_xml(symbolic_data TEXT) RETURNS TEXT AS $$
    from smrpy import symbolic_data_to_m21_xml
    return symbolic_data_to_m21_xml(symbolic_data)
$$ LANGUAGE plpython3u IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION smrpy_excerpt(m21_xml TEXT, nids INTEGER[], measure_start INTEGER, measure_end INTEGER, color TEXT) RETURNS TEXT AS $$
    from smrpy import excerpt
    return excerpt(m21_xml, notes, color)
$$ LANGUAGE plpython3u IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION colored_excerpt(pid INTEGER, nids INTEGER[], color TEXT) RETURNS TEXT AS $$
    WITH mids AS (
        SELECT array_agg(mid ORDER BY mid ASC) AS mids
        FROM unnest(nids) AS nid JOIN Note ON Note.nid = nid.nid
        JOIN MeasureOnsetMap ON Note.n[0] = MeasureOnsetMap.onset
        AND colored_excerpt.pid = MeasureOnsetMap.pid)
    SELECT smrpy_excerpt(Piece.music21_xml, nids, mids[array_lower(mids, 1)], mids[array_upper(mids, 1)], color) FROM Piece JOIN mids ON True WHERE colored_excerpt.pid = Piece.pid;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION generate_notes(symbolic_data TEXT) RETURNS SETOF Note AS $$
    from smrpy import generate_notes
    return generate_notes(symbolic_data)
$$ LANGUAGE plpython3u IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION smrpy_measure_onset_map(symbolic_data TEXT) RETURNS SETOF MeasureOnsetMap AS $$
    from smrpy import measure_onset_map
    return measure_onset_map(symbolic_data)
$$ LANGUAGE plpython3u IMMUTABLE STRICT;
