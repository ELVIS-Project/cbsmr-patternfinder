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

ELVISDUMP = "/Users/davidgarfinkle/elvis-project/elvisdump/"

POSTGRES_CONN_STR = 'host=localhost dbname=postgres user=postgres password=postgres'
CONN = psycopg2.connect(POSTGRES_CONN_STR)
CONN.autocommit = True

PIECES = [(subdir, [os.path.join(ELVISDUMP, subdir, f) for f in os.listdir(os.path.join(ELVISDUMP, subdir))])
            for subdir in ("XML", "MID", "MEI")]

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

def do_insert(pid, fmt, data, path):
    with CONN, CONN.cursor() as cur:
        cur.execute(f"""
            INSERT INTO Piece(pid, fmt, data, path)
            VALUES ('{pid}', '{fmt}', '{data}', '{path}')
            ON CONFLICT (pid) DO UPDATE SET data = '{data}'""")


def existingPieces():
    with CONN, CONN.cursor() as cur:
        cur.execute(f"SELECT pid FROM Piece")
        res = cur.fetchall()
    return [int(tup[0]) for tup in res]

def do_all_inserts(pieces):
    curPieces = existingPieces()
    print(f"We have {len(curPieces)} already in the db")

    for name, it in pieces:
        for piece in tqdm(it):

            piece_id, fmt, name = parse_piece_path(piece)
            if int(piece_id) in curPieces and os.environ.get("SKIP", False) == "true":
                continue

            with open(piece, "rb") as f:
                filebytes = f.read()

            try:
                m21_score = music21.converter.parse(filebytes)
                xml = m21_score_to_xml_write(m21_score) 
                data = base64.b64encode(xml).decode('utf-8')
                do_insert(piece_id, fmt, data, piece)
            except Exception as e:
                do_insert(piece_id, 'failed', 'failed', piece)
                

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
    do_all_inserts(PIECES)

if __name__ == '__main__':
    main()
