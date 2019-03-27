#!/usr/local/bin/python3

from flask import Flask, request, jsonify, Response
from errors import *
from _w2 import ffi, lib
from indexer.insert_piece import insert, indexers
from tqdm import tqdm
import sqlalchemy
import music21
import legacy
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


SCORES = {}
def load_scores():
    print("Selecting pieces from database")
    with CONN, CONN.cursor() as cur:
        cur.execute(f"SELECT vectors, id, name FROM Piece")
        results = cur.fetchall()

    for vectors, idx, name in tqdm(results[:10]):
        SCORES[idx] = lib.init_score(vectors.encode('utf-8'))

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

def filter_chain(chain, window, num_notes):
    return (
        sum((r - l <= window) for l, r in zip(chain, chain[1:])) == len(chain) - 1
        and len(chain) >= num_notes)

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

    print("Parsing query...", end='')
    query_notes = music21.converter.parse(query_str).flat.notes
    df = indexers.legacy_intra_vectors(query_str, 1)
    query_csv = indexers.legacy_intra_vectors_to_csv(df)
    print(query_csv)
    query = lib.init_score(query_csv.encode('utf-8'))

    resp = {'occs': []}
    for idx, target in app.config['SCORES'].items():
        print("Searching " + str(idx))
        res = ffi.new("struct Result*")
        lib.search_return_chains(query, target, res)
        chains = legacy.extract_chains(res.table, target.num_notes)

        print(chains)

        for chain in chains:
            if filter_chain(chain, window=10, num_notes=len(query_notes)):
                resp['occs'].append({
                    'pid': piece_id,
                    'chain': chain
                })

    return jsonify(resp)

def coloured_excerpt(note_list, piece_id):
    note_list = [int(i) for i in note_list]

    with CONN, CONN.cursor() as cur:
        cur.execute(f"""
            SELECT data
            FROM Piece
            WHERE id={piece_id}
            ;
            """)
        results = cur.fetchall()
        if not results:
            print(f"Warning: no piece found at id {piece_id}")
            return results

    score = music21.converter.parse(base64.b64decode(results[0][0]).decode('utf-8'))
    nps = list(indexers.NotePointSet(score))
    nps_ids = [nps[i].original_note_id for i in note_list]

    # Get stream excerpt
    _, start_measure = score.beatAndMeasureFromOffset(nps[note_list[0]].offset)
    _, end_measure = score.beatAndMeasureFromOffset(nps[note_list[-1]].offset + nps[-1].duration.quarterLength - 1)
    excerpt = score.measures(numberStart=start_measure.number, numberEnd=end_measure.number)

    # Colour notes
    for note in excerpt.flat.notes:
        if note.id in nps_ids:
            note.style.color = 'red'

    # Delete part names (midi files have bad data)
    for part in excerpt:
        part.partName = ''

    sx = music21.musicxml.m21ToXml.ScoreExporter(excerpt)
    musicxml = sx.parse()

    from io import StringIO
    import sys
    bfr = StringIO()
    sys.stdout = bfr
    sx.dump(musicxml)
    output = bfr.getvalue()
    sys.stdout = sys.__stdout__

    return output


@app.route("/excerpt", methods=["GET"])
def excerpt():
    """
    Returns a highlighted excerpt of a score
    """
    piece_id = request.args.get("piece_id")
    notes = request.args.get("notes").split(",")

    excerpt_xml = coloured_excerpt(notes, piece_id)
    return Response(excerpt_xml, mimetype='text/xml')

    


if __name__ == '__main__':
    load_scores()
    app.config['SCORES'] = SCORES
    app.run(host="0.0.0.0", port=80)
