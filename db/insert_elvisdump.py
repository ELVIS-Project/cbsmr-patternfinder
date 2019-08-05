import sys
import os
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'proto'))

import io
import base64
import psycopg2
import grpc
import smr_pb2, smr_pb2_grpc
import music21
from tqdm import tqdm

POSTGRES_CONN_STR = "host={} dbname=postgres user=postgres password=postgres".format(os.getenv("PG_HOST"))
CONN = psycopg2.connect(POSTGRES_CONN_STR)
CONN.autocommit = True

ELVISDUMP = os.getenv("ELVISDUMP")
def get_elvis_pieces():
    if ELVISDUMP:
        return [(subdir, [os.path.join(ELVISDUMP, subdir, f) for f in os.listdir(os.path.join(ELVISDUMP, subdir))])
                    for subdir in ("XML", "MID", "MEI")]
    else:
        return None

def parse_piece_path(piece_path):
    basename, fmt = os.path.splitext(os.path.basename(piece_path))
    fmt = fmt[1:] # skip '.'
    base = [x for x in os.path.basename(basename).split("_") if not "file" in x]

    piece_id = base[0]
    name = base[1]

    return piece_id, fmt, name

def create_piece_table():
    with CONN, CONN.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Piece (
                pid SERIAL PRIMARY KEY,
                fmt VARCHAR(8),
                data TEXT,
                path TEXT)
            ;
            """)

def db_insert(pid, fmt, data, path):
    with CONN, CONN.cursor() as cur:
        insert = "INSERT INTO Piece(pid, fmt, data, path)"
        values = "VALUES('{}', '{}', '{}', '{}')".format(pid, fmt, data, path)
        conflict = "ON CONFLICT (pid) DO UPDATE SET data = '{}'".format(data)
        cur.execute(insert + values + conflict)

def existingPieces():
    with CONN, CONN.cursor() as cur:
        cur.execute("SELECT pid FROM Piece")
        res = cur.fetchall()
    return [int(tup[0]) for tup in res]

def do_one_insert(piece):
    piece_id, fmt, name = parse_piece_path(piece)
    with open(piece, "rb") as f:
        filebytes = f.read()

    try:
        m21_score = music21.converter.parse(filebytes)
        xml = m21_score_to_xml_write(m21_score)
        data = base64.b64encode(xml).decode('utf-8')
        db_insert(piece_id, fmt, data, piece)
    except Exception as e:
        db_insert(piece_id, 'failed', 'failed', piece)

def do_all_inserts(pieces):
    curPieces = existingPieces()
    print("We have {} already in the db".format(len(curPieces)))

    for subfolder, it in pieces:
        for piece in tqdm(it):

            piece_id, fmt, name = parse_piece_path(piece)
            if int(piece_id) in curPieces and os.environ.get("SKIP", False) == "true":
                continue
            else:
                do_one_insert(piece)

def m21_score_to_xml_sx(m21_score):
    sx = music21.musicxml.m21ToXml.ScoreExporter(m21_score)
    musicxml = sx.parse()

    bfr = io.StringIO()
    sys.stdout = bfr
    sx.dump(musicxml)
    output = bfr.getvalue()
    sys.stdout = sys.__stdout__

    return output

def m21_score_to_xml_write(m21_score):
    o = m21_score.write('xml')
    with open(o, 'rb') as f:
        xml = f.read()
    os.remove(o)
    return xml

def main():
    create_piece_table()
    for p in sys.argv[1:]:
        print("inserting {}...".format(p))
        do_one_insert(p)

if __name__ == '__main__':
    main()
