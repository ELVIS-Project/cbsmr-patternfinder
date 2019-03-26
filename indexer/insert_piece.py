import sys
import os
import io
import csv
import psycopg2
import base64
from indexer.client import index_piece
from indexer import indexers

ELVIS_DUMP="/Users/davidgarfinkle/elvis-project/elvisdump"

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
    return (x, y, left.pieceIdx, right.pieceIdx, left.pitchB40, right.pitchB40, y, y)

def notes_to_vectors_csv(piece_id, pb_notes):
    values = []
    pb_notes.sort(key = lambda x: (x.onset, x.pitchB40))
    for i in range(len(pb_notes)):
        for j in range(i, min(i + WINDOW, len(pb_notes))):
            values.append(notes_to_vector(pb_notes[i], pb_notes[j]))

    file_obj = io.StringIO()
    csv_writer = csv.writer(file_obj, delimiter=',')
    csv_writer.writerow(['x', 'y', 'startIndex', 'endIndex', 'startPitch', 'endPitch', 'diatonicDiff', 'chromaticDiff'])
    csv_writer.writerow([len(pb_notes)])
    csv_writer.writerow([len(values)])

    for vec in values:
        csv_writer.writerow([str(v) for v in vec])

    output = file_obj.getvalue()
    file_obj.close()
    return output

def notes_to_trigrams_sql(pb_notes):
    trigrams = []

    # Combinatorial explosion
    for i in range(len(pb_notes)):
        for j in range(i, min(WINDOW, len(pb_notes))):
            for k in range(j, min(WINDOW, len(pb_notes))):
                trigrams.append((pb_notes[i], pb_notes[j], pb_notes[k]))

    return [f"""
            INSERT INTO Trigram (pitches, document_frequency)
            VALUES ('{'{' + ",".join(str(n.pitchB40) for n in trigram) + '}'}', 1)
            ON CONFLICT (pitches)
            DO UPDATE SET document_frequency = Trigram.document_frequency + 1;
        """ for trigram in trigrams]

def insert(path, conn):
    piece_id, name, composer, corpus, encoding = indexers.parse_piece_path(path)

    response = index_piece(path, name, encoding)

    with open(path, 'rb') as f:
        symbolic_data = base64.b64encode(f.read()).decode('utf-8')

    with conn, conn.cursor() as cur:
        cur.execute(f"INSERT INTO Piece (id, name, data) VALUES ('{piece_id}', '{name}', '{symbolic_data}') ON CONFLICT (id) DO NOTHING;")

        for pb_note in response.notes:
            cur.execute(note_to_sql(piece_id, pb_note))

        cur.execute(f"UPDATE Piece SET vectors='{notes_to_vectors_csv(piece_id, response.notes)}' WHERE id={piece_id}")

        for trigram_insert_sql in notes_to_trigrams_sql(response.notes):
            cur.execute(trigram_insert_sql)

        for pb_measure in response.measures:
            cur.execute(measure_to_sql(piece_id, pb_measure))


if __name__ == '__main__':
    subdirs = ("MEI", "MID", "XML")

    path = sys.argv[1]

    POSTGRES_CONN_STR = 'host=localhost dbname=postgres user=postgres password=postgres'
    CONN = psycopg2.connect(POSTGRES_CONN_STR)

    if path in subdirs:
        from tqdm import tqdm
        subdir_path = os.path.join(os.path.abspath(ELVIS_DUMP), path)

        for fname in tqdm(os.listdir(subdir_path)):
            fullpath = os.path.join(subdir_path, fname)
            insert(fullpath, CONN)
    else:
        insert(path, CONN)