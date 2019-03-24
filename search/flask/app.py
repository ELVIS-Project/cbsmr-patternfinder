#!/usr/local/bin/python3

from flask import Flask, request, jsonify
from errors import *
from _w2 import ffi, lib
from indexer.insert_piece import insert, indexers
import sqlalchemy
import music21
import psycopg2
import base64

app = Flask(__name__)

#POSTGRES_CONN_STR = "postgresql://indexer:indexer@localhost:5432/postgres"
#engine = sqlalchemy.create_engine(POSTGRES_CONN_STR)
POSTGRES_CONN_STR = 'host=localhost dbname=postgres user=postgres password=postgres'

try:
	CONN = psycopg2.connect(POSTGRES_CONN_STR)
except Exception as e:
	import time
	time.sleep(7)
	CONN = psycopg2.connect(POSTGRES_CONN_STR)
CONN.autocommit = False

@app.route("/")
def root():
    return "Hello World!"

@app.route("/index/<piece_id>", methods=["GET", "POST"])
def index_id(piece_id):
    """
    Indexes a piece and stores it at :param id
    """
    piece_id = int(piece_id)
    if request.method == "POST":
        insert(piece_id, CONN)

    return "yay!", 200

def extract_chain(c_array):
    i = 0
    note_indices = []
    while c_array[i] != 0 and c_array[i] != '\0':
        note_indices.append(c_array[i])
        i += 1
    return note_indices

def filter_chain(chain, window):
    return sum((r - l <= window) for l, r in zip(chain, chain[1:])) == len(chain) - 1

def query_measures(chain, piece_id):
    with CONN, CONN.cursor() as cur:
        cur.execute(f"""
            SELECT DISTINCT (data) FROM Measure JOIN Note
            ON Measure.onset = Note.onset
            WHERE Note.piece_id = {piece_id} AND Note.piece_idx IN {tuple(chain)} AND Measure.pid={piece_id};
        """)
        return [res[0] for res in cur.fetchall()]
        
@app.route("/search", methods=["GET"])
def search_all():
    """
    Searches entire database for the query string
    """
    query_str = request.args.get("query")

    df = indexers.legacy_intra_vectors(query_str, 1)
    query_csv = indexers.legacy_intra_vectors_to_csv(df)

    with CONN, CONN.cursor() as cur:
        cur.execute(f"SELECT vectors, id FROM Piece")
        target_csv_list = cur.fetchall()

    resp = {'chains' : [], 'measures': []}
    for target_csv, piece_id in target_csv_list:
        print(piece_id)
        res = ffi.new("struct Result*")
        result = lib.search_return_chains(query_csv.encode('utf-8'), target_csv.encode('utf-8'), res)

        for i in range(res.num_occs):
            chain = extract_chain(res.chains[i])
            if filter_chain(chain, 10):
                resp['chains'].append(chain)
                resp['measures'].append(query_measures(chain, piece_id))

    return jsonify(resp)

def coloured_excerpt(note_list, piece_id):
    excerpt = music21.stream.Stream()
    score_note_ids = []

    with CONN, CONN.cursor() as cur:
        cur.execute(f"""
            SELECT data, nid, mid
            FROM Measure
            WHERE pid={piece_id} AND nid BETWEEN {note_list[0]} AND {note_list[-1]}
            ORDER BY mid
            ;
            """)
        results = cur.fetchall()
        if not results:
            print(f"Warning: no measures found for piece {piece_id} btwn notes {note_list[0]} and {note_list[-1]}")
            return results

    _, _, start_mid = results[0]
    _, _, end_mid = results[-1]
    cur = start_mid
    newOffset = 0

    for i in range(len(results)):
        measure_data, nid, mid = results[i]
        m21_measure = music21.converter.parse(base64.b64decode(measure_data))
        print("inserting")
        excerpt.insert(newOffset, m21_measure)

        if i < len(results) - 1:
            _, _, next_mid = results[i + 1]
            if next_mid > cur:
                newOffset += m21_measure.duration.quarterLength
                cur += 1

    nps = indexers.NotePointSet(excerpt)
    note_list_from_measure_start = [n - results[0][1] for n in note_list]
    score_note_ids.extend([nps[i].original_note_id for i in note_list_from_measure_start])
        
    for note in excerpt.flat.notes:
        if note.id in score_note_ids:
            note.style.color = 'red'
    
    excerpt_out = excerpt.write('xml')
    with open(excerpt_out, 'r') as f:
        excerpt_xml = f.read()

    return excerpt


@app.route("/excerpt", methods=["GET"])
def excerpt():
    """
    Returns a highlighted excerpt of a score
    """
    piece_id = request.args.get("piece_id")
    notes = request.args.get("notes").split(",")

    excerpt = coloured_excerpt(notes, piece_id)
    return Response(excerpt_xml, mimetype='text/xml')

    


if __name__ == '__main__':
    print("main")
    #app.run(host="0.0.0.0", port=80)
