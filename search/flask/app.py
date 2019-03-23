#!/usr/local/bin/python3

from flask import Flask, request, jsonify
from errors import *
from _w2 import ffi, lib
import indexers
import sqlalchemy
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

@app.route("/index", methods=["GET", "POST"])
def index():
    """
    Indexes a piece with ALL available indexers
    """
    if request.method == "POST":
        return "yay", 200

def is_piece_in_db(piece_id):
    with CONN, CONN.cursor() as cur:
        cur.execute(
            f"""
                SELECT id FROM Piece WHERE id={piece_id};
            """
        )
        return cur.rowcount == 1

@app.route("/index/<piece_id>", methods=["GET", "POST"])
def index_id(piece_id):
    """
    Indexes a piece and stores it at :param id
    """
    piece_id = int(piece_id)
    if request.method == "POST":
        data = request.get_data()
        #data = base64.b64decode(data).decode('utf-8')
        if is_piece_in_db(piece_id) is True:
            return "piece already in db", 400
        try:
            print("notes...")
            notes = indexers.notes(data)
            print("vectors...")
            legacy_intra_vectors = indexers.legacy_intra_vectors(data, 4)
        except Exception as e:
            raise IndexerError from e

        with CONN, CONN.cursor() as cur:
            print("inserting to db...")
            try:
                csv_vectors = indexers.legacy_intra_vectors_to_csv(legacy_intra_vectors)
                cur.execute(
                    f"""
                    INSERT INTO Piece (id, vectors)
                    VALUES ({piece_id}, '{csv_vectors}');
                    """
                )
                cur.execute(indexers.notes_to_sql(notes, piece_id))
                print("measures...")
                indexers.index_and_insert_measures(data, piece_id, CONN)
            except Exception as e:
                print(f"Failed to enter {piece_id}: \n{str(e)}")
                return "no", 500

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
        cur.execute(f"SELECT data, nid FROM Measure WHERE pid={piece_id} AND nid BETWEEN {note_list[0]} AND {note_list[-1]}")
        results = cur.fetchall()

    for measure_data, nid in results:
        measure = music21.converter.parse(base64.b64decode(measure_data))
        excerpt.append(measure)

        nps = indexers.NotePointSet(measure)
        note_list_from_measure_start = [n - nid for n in note_list]
        score_note_ids.extend([nps[i].original_note_id for i in note_list_from_measure_start])
        
    for note in excerpt.flat.notes:
        if note.id in score_note_ids:
            note.style.color = 'red'
    
    excerpt_out = excerpt.write('xml')
    with open(excerpt_out, 'rb') as f:
        excerpt_encoded = base64.b64encode(f.read()).decode('utf-8')

    return excerpt_encoded


@app.route("/excerpt", methods=["GET"])
def excerpt():
    """
    Returns a highlighted excerpt of a score
    """
    piece_id = request.args.get("piece_id")
    notes = request.args.get("notes").split(",")

    


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
