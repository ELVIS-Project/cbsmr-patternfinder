#!/usr/local/bin/python3
import sys
import os
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir))
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'proto'))
CURDIR = os.path.abspath(os.path.dirname(__file__))

from flask import Flask, request, jsonify, Response, send_from_directory, url_for, render_template
from errors import *
from occurrence import filter_occurrences, OccurrenceFilters
import indexers
import music21
import psycopg2
import base64
import time

import grpc
from proto import smr_pb2, smr_pb2_grpc

from response import build_response

application = Flask(__name__)

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
    return send_from_directory('templates', path)

def m21_score_to_xml_write(m21_score):
    o = m21_score.write('xml')
    with open(o, 'rb') as f:
        xml = f.read()
    os.remove(o)
    return xml

@application.route("/index/<piece_id>", methods=["POST"])
def index_id(piece_id):
    """
    Indexes a piece and stores it at :param id
    """
    db_conn = application.config['PSQL_CONN']

    if not piece_id:
        return Response("POST /index/<piece_id> requires an integer argument", status=400)
    try:
        piece_id = int(piece_id)
    except ValueError as e:
        return Response(f"POST /index/<piece_id> requires an integer argument; tried parsing, failed with {str(e)}", status=400)

    # :ref https://werkzeug.palletsprojects.com/en/0.14.x/request_data/#how-does-it-parse
    if request.content_type == "multipart/form-data":
        files = list(request.file.items())
        # `request.file` will be a MultiDict object
        # :ref https://werkzeug.palletsprojects.com/en/0.15.x/datastructures/#werkzeug.datastructures.MultiDict
        if len(files) > 1:
            return Response(
                    f"POST /index/<piece_id> only accepts one file at a time, \
                    but received a multipart/form-data POST with {len(files)} files", status=415)
        else:
            symbolic_data = files[0]
    elif request.content_type == "application/x-www-form-urlencoded":
        return Response("TODO; Content-Type: application/x-www-form-urlencoded is unsupported", status=415)
    else:
        symbolic_data = request.data
    if not symbolic_data:
        return Response("Failed to find piece data in POST request body", status=400)

    try:
        m21_score = indexers.parse(symbolic_data)
    except Exception as e:
        return Response(f"failed to parse symbolic data with music21: {str(e)}", status=415)

    xml = m21_score_to_xml_write(m21_score)
    data = base64.b64encode(xml).decode('utf-8')
    with db_conn, db_conn.cursor() as cur:
        cur.execute(f"INSERT INTO Piece (pid, data) VALUES ('{piece_id}', '{data}') ON CONFLICT ON CONSTRAINT piece_pkey DO UPDATE SET data = '{data}';")

    sc = indexers.parse(xml)
    pb_notes = indexers.pb_notes(sc)

    with grpc.insecure_channel(application.config['SMR_URI']) as channel:
        stub = smr_pb2_grpc.SmrStub(channel)
        response = stub.AddPiece(smr_pb2.AddPieceRequest(pid = piece_id, notes = pb_notes))

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

    for arg in ("page", "rpp", "query", "tnps", "intervening"):
        missing = []
        if not request.args.get(arg):
            missing.append(arg)
        if missing:
            return Response(f"Missing GET parameter(s): {missing}", status=400)

    try:
        page = int(request.args.get("page"))
        rpp = int(request.args.get("rpp"))
        tnps = request.args.get("tnps").split(",")
        intervening = int(request.args.get("intervening"))
    except ValueError as e:
        return Response(f"Failed to parse parameter(s) to integer, got exception {str(e)}", status=400)

    query_str = request.args.get("query")

    query_score = indexers.parse(query_str)
    query_pb_notes = indexers.pb_notes(query_score)

    try:
        with grpc.insecure_channel(application.config['SMR_URI']) as channel:
            stub = smr_pb2_grpc.SmrStub(channel)
            response = stub.Search(smr_pb2.SearchRequest(notes=query_pb_notes))
    except Exception as e:
        return Response(f"failed to search: {str(e)}", status=500)

    occfilters = OccurrenceFilters(
            transpositions = [int(x) for x in tnps],
            intervening = intervening)

    search_response = build_response(
            application.config['PSQL_CONN'],
            filter_occurrences(response.occurrences, query_pb_notes, occfilters),
            rpp,
            page,
            query_str)

    if request.content_type == "application/json":
        return jsonify(search_response)
    else:
        return render_template("search.html", searchResponse = search_response)

def main():
    application.run(host="0.0.0.0", port=int(os.environ['FLASK_PORT']))

if __name__ == '__main__':
    main()
