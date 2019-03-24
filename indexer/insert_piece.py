import sys
import os
import io
import csv
import psycopg2
from client import index_piece
from indexer import indexers

WINDOW = 10

def note_to_sql(piece_id, pb_note):
    return f"""
        INSERT INTO Note (pid, pidx, onset, "offset", "pitchb40")
        VALUES ('{piece_id}', '{pb_note.pieceIdx}', '{pb_note.onset}', '{pb_note.offset}', '{pb_note.pitchB40}')
        ON CONFLICT (pid, pidx) DO NOTHING
        ;
        """

def measure_to_sql(piece_id, pb_measure):
    return f"""
        INSERT INTO Measure (pid, mid, nid, data)
        VALUES ('{piece_id}', '{pb_measure.number}', '{pb_measure.noteIdx}', '{pb_measure.symbolicData.decode('utf-8')}')
        ;
    """
    #SELECT '{piece_id}', '{pb_measure.number}', '{pb_measure.noteIdx}', '{pb_measure.symbolicData.decode('utf-8')}'
    #WHERE NOT EXISTS (SELECT NULL FROM Measure WHERE pid={piece_id} AND mid={pb_measure.number});

def notes_to_vector(left, right):
    x = right.onset - left.onset
    y = right.pitchB40 - left.pitchB40
    return (x, y, left.pieceIdx, right.pieceIdx, left.pitchB40, right.pitchB40)

def notes_to_vectors_csv(piece_id, pb_notes):
    values = []
    pb_notes.sort(key = lambda x: (x.onset, x.pitchB40))
    for i in range(len(pb_notes)):
        for j in range(1, WINDOW):
            values.append(notes_to_vector(pb_notes[i], pb_notes[j]))

    file_obj = io.StringIO()
    csv_writer = csv.writer(file_obj, delimiter=',')
    csv_writer.writerow(['x', 'y', 'startIndex', 'endIndex', 'startPitch', 'endPitch', 'diatonicDiff', 'chromaticDiff'])
    csv_writer.writerow([len(pb_notes)])
    csv_writer.writerow([len(values)])

    for vec in values:
        csv_writer.writerow(",".join(str(v) for v in vec))

    output = file_obj.getvalue()
    file_obj.close()
    return output

def piece_to_sql(piece_id, csv_vectors):

    return f"""
    INSERT INTO Piece (id, vectors)
    VALUES ({piece_id}, '{csv_vectors}')
    ;
    """

def insert(piece_id, conn, name="", encoding=""):
    response = index_piece(path, name, encoding)

    with conn, conn.cursor() as cur:
        cur.execute(f"INSERT INTO Piece (id) VALUES ({piece_id}) ON CONFLICT (id) DO NOTHING;")

        for pb_note in response.notes:
            cur.execute(note_to_sql(piece_id, pb_note))

        cur.execute(f"UPDATE Piece SET vectors='{notes_to_vectors_csv(piece_id, response.notes)}' WHERE id={piece_id}")

        for pb_measure in response.measures:
            cur.execute(measure_to_sql(piece_id, pb_measure))


if __name__ == '__main__':
    path = sys.argv[1]
    piece_id, name, composer, corpus, encoding = indexers.parse_piece_path(path)

    POSTGRES_CONN_STR = 'host=localhost dbname=postgres user=postgres password=postgres'
    CONN = psycopg2.connect(POSTGRES_CONN_STR)

    insert(piece_id, CONN, name, encoding)

"""
    return f
        INSERT INTO legacy_intra_vectors (piece_id, x, y, startIndex, endIndex, startPitch, endPitch, diatonicDiff, chromaticDiff)
        {",".join(
            f"('{piece_id}', '{x}', '{y}', '{start}', '{end}', '{startPitch}', '{endPitch}', '{y}', '{y}')")
            for x, y, start, end, startPitch, endPitch in values}
"""