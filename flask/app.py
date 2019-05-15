#!/usr/local/bin/python3
import sys
import os
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'conf'))
CURDIR = os.path.abspath(os.path.dirname(__file__))

from flask import Flask, request, jsonify, Response, send_from_directory, url_for, render_template
from errors import *
from tqdm import tqdm
import music21
import psycopg2
import base64
import time

import grpc
from proto import smr_pb2, smr_pb2_grpc

from indexer import indexers
from response import build_response

application = Flask(__name__)

application.config['INDEXER_URI'] = f"{os.environ['INDEXER_HOST']}:{os.environ['INDEXER_PORT']}"
application.config['SMR_URI'] = f"{os.environ['SMR_HOST']}:{os.environ['SMR_PORT']}"

def connect_to_psql():
    db_str = ' '.join('='.join((k, os.environ[v])) for k, v in (
                ('host', 'PG_HOST'),
                ('port', 'PG_PORT'),
                ('dbname', 'PG_DB'),
                ('user', 'PG_USER'),
                ('password', 'PG_PASS')))
    print("connecting to " + db_str)

    while True:
        try:
            conn = psycopg2.connect(db_str)
            break
        except Exception as e:
            time_to_wait = 5
            print(f"failed; waiting {time_to_wait} seconds...")
            time.sleep(time_to_wait)
            connect_to_psql()
    conn.autocommit = False

    application.config['PSQL_CONN'] = conn
print("connecting to pg")
connect_to_psql()

@application.route("/", methods=["GET"])
def index():
    return render_template("search.html", searchResponse = {})

@application.route("/dist/<path>", methods=["GET"])
def get_dist(path):
    return send_from_directory(os.environ['WEB_DIST'], path)

@application.route("/index/<piece_id>", methods=["POST"])
def index_id(piece_id):
    """
    Indexes a piece and stores it at :param id
    """
    db_conn = application.config['PSQL_CONN']
    piece_id = int(piece_id)
    if request.method == "POST":
        symbolic_data = base64.b64encode(request.data).decode('utf-8')
        with db_conn, db_conn.cursor() as cur:
            cur.execute(f"INSERT INTO Piece (pid, data) VALUES ('{piece_id}', '{symbolic_data}') ON CONFLICT ON CONSTRAINT piece_pkey DO NOTHING;")

        with grpc.insecure_channel(application.config['INDEXER_URI']) as channel:
            stub = smr_pb2_grpc.IndexStub(channel)
            pb_notes = stub.IndexNotes(smr_pb2.IndexRequest(symbolic_data = request.data))

        with grpc.insecure_channel(application.config['SMR_URI']) as channel:
            stub = smr_pb2_grpc.SmrStub(channel)
            response = stub.AddPiece(smr_pb2.AddPieceRequest(id = piece_id, notes = pb_notes))

    return Response(str(piece_id), mimetype='text/plain')


@application.route("/excerpt", methods=["GET"])
def excerpt():
    """
    Returns a highlighted excerpt of a score
    """
    piece_id = request.args.get("pid")
    notes = request.args.get("nid").split(",")

    excerpt_xml = coloured_excerpt(application.config["PSQL_CONN"], notes, piece_id)
    return Response(excerpt_xml, mimetype='text/xml')


@application.route("/search", methods=["GET"])
def search():

    if not request.args.get("query"):
        return render_template("search.html", searchResponse = {})

    page = request.args.get("page")
    rpp = request.args.get("rpp")
    query_str = request.args.get("query")
    if not query_str:
        return "No query parameter included in GET request", 400
    elif not page or not rpp:
        return "missing GET parameters", 400
    else:
        page = int(page)
        rpp = int(rpp)

    query_bytes = bytes(query_str, encoding='utf-8')

    with grpc.insecure_channel(application.config['INDEXER_URI']) as channel:
        stub = smr_pb2_grpc.IndexStub(channel)
        pb_notes = stub.IndexNotes(smr_pb2.IndexRequest(symbolic_data = query_bytes, encoding = smr_pb2.IndexRequest.UTF8))

    with grpc.insecure_channel(application.config['SMR_URI']) as channel:
        stub = smr_pb2_grpc.SmrStub(channel)
        response = stub.Search(pb_notes)

    return render_template("search.html", searchResponse = build_response(application.config['PSQL_CONN'], response.occurrences, rpp, page, query_str))

def main():
    application.run(host="0.0.0.0", port=int(os.environ['FLASK_PORT']))

if __name__ == '__main__':
    main()
