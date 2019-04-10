#!/usr/local/bin/python3
import os
import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'proto'))

from flask import Flask, request, jsonify, Response, send_from_directory, url_for, render_template
from errors import *
from tqdm import tqdm
import music21
import psycopg2
import base64
import os
import json

import grpc
import smr_pb2, smr_pb2_grpc

from indexer import indexers

app = Flask(__name__)

POSTGRES_CONN_STR = 'host=localhost dbname=postgres user=postgres password=postgres'

try:
	CONN = psycopg2.connect(os.environ.get('SMR_DB_STRING', POSTGRES_CONN_STR))
except Exception as e:
	import time
	time.sleep(7)
	CONN = psycopg2.connect(os.environ.get('SMR_DB_STRING', POSTGRES_CONN_STR))
CONN.autocommit = False

@app.route("/dist/<path>", methods=["GET"])
def get_dist(path):
    return send_from_directory("/Users/davidgarfinkle/elvis-project/cbsmr-patterfinder/webclient/dist", path)

@app.route("/index/<piece_id>", methods=["POST"])
def index_id(piece_id):
    """
    Indexes a piece and stores it at :param id
    """
    piece_id = int(piece_id)
    if request.method == "POST":
        symbolic_data = base64.b64encode(request.data).decode('utf-8')
        with CONN, CONN.cursor() as cur:
            cur.execute(f"INSERT INTO Piece (id, data) VALUES ('{piece_id}', '{symbolic_data}') ON CONFLICT (id) DO NOTHING;")

        with grpc.insecure_channel('localhost:50051') as channel:
            stub = smr_pb2_grpc.IndexStub(channel)
            pb_notes = stub.IndexNotes(smr_pb2.IndexRequest(symbolic_data = request.data))

        with grpc.insecure_channel('localhost:8080') as channel:
            stub = smr_pb2_grpc.SmrStub(channel)
            response = stub.AddPiece(smr_pb2.AddPieceRequest(id = piece_id, notes = pb_notes))

    return Response(str(piece_id), mimetype='text/plain')

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
    piece_id = request.args.get("pid")
    notes = request.args.get("nid").split(",")

    excerpt_xml = coloured_excerpt(notes, piece_id)
    return Response(excerpt_xml, mimetype='text/xml')


def pb_occ_to_excerpt_url(pb_occ):
    return url_for("excerpt", pid=pb_occ.pid, nid=",".join(str(x) for x in pb_occ.notes))

def generate_response(occs, rpp, page):
    num_pages = int(len(occs) / rpp) + 1
    return {
        'total': len(occs),
        'num_pages': num_pages,
        #'pages': [[pb_occ_to_excerpt_url(o) for o in occs[rpp * i : rpp * (i + 1)]] for i in range(num_pages)]
        'pages': [
            [
                {
                    'pid': o.pid,
                    'nid': [int(n) for n in o.notes]
                }
                for o in occs[rpp * i : rpp * (i + 1)]]
            for i in range(num_pages)]
    }

@app.route("/search", methods=["GET"])
def search():
    page = int(request.args.get("page"))
    rpp = int(request.args.get("rpp"))
    query_str = request.args.get("query")
    if not query_str:
        return "No query parameter included in GET request", 400

    query_bytes = bytes(query_str, encoding='utf-8')

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = smr_pb2_grpc.IndexStub(channel)
        pb_notes = stub.IndexNotes(smr_pb2.IndexRequest(symbolic_data = query_bytes, encoding = smr_pb2.IndexRequest.UTF8))

    with grpc.insecure_channel('localhost:8080') as channel:
        stub = smr_pb2_grpc.SmrStub(channel)
        response = stub.Search(pb_notes)

    print(response.occurrences)
    #return Response("\n".join(pb_occ_to_excerpt_url(occ) for occ in response.occurrences), mimetype="uri-list")
    #return send_from_directory('/Users/davidgarfinkle/elvis-project/cbsmr-patterfinder/webclient/src', 'search.html')
    return render_template("search.html", searchResponse = generate_response(response.occurrences, rpp, page))
    #return jsonify(generate_response(response.occurrences, rpp, page))

if __name__ == '__main__':
    #load_scores()
    #app.config['SCORES'] = SCORES
    app.run(host="0.0.0.0", port=80)
