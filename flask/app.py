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
import json

import grpc
from proto import smr_pb2, smr_pb2_grpc

from indexer import indexers
from excerpt import coloured_excerpt

app = Flask(__name__)

def connect_to_psql():
    db_str = ' '.join('='.join((k, os.environ[v])) for k, v in (
                ('host', 'PG_HOST'),
                ('port', 'PG_PORT'),
                ('dbname', 'PG_DB'),
                ('user', 'PG_USER'),
                ('password', 'PG_PASS')))
    print("connecting to " + db_str)

    unconnected = True
    while unconnected:
        try:
            conn = psycopg2.connect(db_str)
            unconnected = False
        except Exception as e:
            import time
            time.sleep(5)
            conn = psycopg2.connect(db_str)
    conn.autocommit = False

    app.config['PSQL_CONN'] = conn

@app.route("/", methods=["GET"])
def index():
    return Response("Hello, World!", mimetype="text/plain")

@app.route("/dist/<path>", methods=["GET"])
def get_dist(path):
    return send_from_directory(os.environ['WEB_DIST'], path)

@app.route("/index/<piece_id>", methods=["POST"])
def index_id(piece_id):
    """
    Indexes a piece and stores it at :param id
    """
    db_conn = app.config['PSQL_CONN']
    piece_id = int(piece_id)
    if request.method == "POST":
        symbolic_data = base64.b64encode(request.data).decode('utf-8')
        with db_conn, db_conn.cursor() as cur:
            cur.execute(f"INSERT INTO Piece (pid, data) VALUES ('{piece_id}', '{symbolic_data}') ON CONFLICT (pid) DO NOTHING;")

        with grpc.insecure_channel(app.config['INDEXER_URI']) as channel:
            stub = smr_pb2_grpc.IndexStub(channel)
            pb_notes = stub.IndexNotes(smr_pb2.IndexRequest(symbolic_data = request.data))

        with grpc.insecure_channel(app.config['SMR_URI']) as channel:
            stub = smr_pb2_grpc.SmrStub(channel)
            response = stub.AddPiece(smr_pb2.AddPieceRequest(id = piece_id, notes = pb_notes))

    return Response(str(piece_id), mimetype='text/plain')


@app.route("/excerpt", methods=["GET"])
def excerpt():
    """
    Returns a highlighted excerpt of a score
    """
    piece_id = request.args.get("pid")
    notes = request.args.get("nid").split(",")

    excerpt_xml = coloured_excerpt(app.config["PSQL_CONN"], notes, piece_id)
    return Response(excerpt_xml, mimetype='text/xml')

def pb_occ_to_json(pb_occ, get_excerpt):
    resp = {
        "excerptFailed": False,
        "pid": pb_occ.pid
    }
    if get_excerpt:
        try:
            xml = coloured_excerpt(app.config["PSQL_CONN"], pb_occ.notes, pb_occ.pid)
        except Exception as e:
            b64_xml = "excerpt failed: " + str(e)
            resp["excerptFailed"] = True
        else:
            b64_xml = base64.b64encode(bytes(xml, encoding='utf-8')).decode('utf-8')
    else:
        b64_xml = ""

    resp["url"] = url_for("excerpt", pid=pb_occ.pid, nid=",".join(str(x) for x in pb_occ.notes))
    resp["xmlBase64"] = b64_xml
    return json.dumps(resp)

def generate_response(occs, rpp, page, query):
    num_pages = int(len(occs) / rpp) + 1
    return {
        'total': len(occs),
        'num_pages': num_pages,
        'query': query,
        'rpp': rpp,
        'pages': [
            [pb_occ_to_json(o, get_excerpt = (i == page)) for o in occs[rpp * i : rpp * (i + 1)]]
            for i in range(num_pages)]
    }

@app.route("/search", methods=["GET"])
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

    with grpc.insecure_channel(app.config['INDEXER_URI']) as channel:
        stub = smr_pb2_grpc.IndexStub(channel)
        pb_notes = stub.IndexNotes(smr_pb2.IndexRequest(symbolic_data = query_bytes, encoding = smr_pb2.IndexRequest.UTF8))

    with grpc.insecure_channel(app.config['SMR_URI']) as channel:
        stub = smr_pb2_grpc.SmrStub(channel)
        response = stub.Search(pb_notes)

    #return Response("\n".join(pb_occ_to_excerpt_url(occ) for occ in response.occurrences), mimetype="uri-list")
    #return send_from_directory('/Users/davidgarfinkle/elvis-project/cbsmr-patternfinder/webclient/src', 'search.html')
    return render_template("search.html", searchResponse = generate_response(response.occurrences, rpp, page, query_str))
    #return jsonify(generate_response(response.occurrences, rpp, page))

if __name__ == '__main__':
    app.config['INDEXER_URI'] = f"{os.environ['INDEXER_HOST']}:{os.environ['INDEXER_PORT']}"
    app.config['SMR_URI'] = f"{os.environ['SMR_HOST']}:{os.environ['SMR_PORT']}"
    connect_to_psql()
    app.run(host="0.0.0.0", port=int(os.environ['FLASK_PORT']))
