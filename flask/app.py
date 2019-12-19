#!/usr/local/bin/python3
import sys
import os
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir))
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'proto'))
CURDIR = os.path.abspath(os.path.dirname(__file__))

from flask import Flask, request, jsonify, Response, send_from_directory, url_for, render_template
from errors import *
from smrpy import occurrence, piece, metadata
from binascii import unhexlify
from dataclasses import dataclass, fields
import json
import indexers
import music21
import psycopg2
import base64
import time

import grpc
from proto import smr_pb2, smr_pb2_grpc
from response import build_response, build_sql_response, QueryArgs

application = Flask(__name__)
logger = application.logger

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
    return conn

@application.route("/", methods=["GET"])
def index():
    return render_template("search.html", searchResponse = {})

@application.route("/dist/<path>", methods=["GET"])
def get_dist(path):
    return send_from_directory('templates', path)

@application.route("/favicon.ico", methods=["GET"])
def get_favicon():
    return send_from_directory('templates', 'favicon.ico')

def m21_score_to_xml_write(m21_score):
    o = m21_score.write('xml')
    with open(o, 'rb') as f:
        xml = f.read()
    os.remove(o)
    return xml

@application.route("/index", methods=["POST"])
def index_no_oarg():
    return index(None)

@application.route("/index/<piece_id>", methods=["POST"])
def index_with_arg(piece_id):
    try:
        piece_id = int(piece_id)
    except ValueError as e:
        return Response(f"POST /index/<piece_id> requires an integer argument; tried parsing, failed with {str(e)}", status=400)
    return index(piece_id)

def index(piece_id):
    """
    Indexes a piece and stores it at :param id
    """
    print("connecting to pg")
    db_conn = connect_to_psql()

    symbolic_data = None
    metadata_dict = {}

    # :ref https://werkzeug.palletsprojects.com/en/0.14.x/request_data/#how-does-it-parse
    if request.content_type == "multipart/form-data":
        # :todo can't get this working. request.files and request.forms is always empty
        # :ref https://github.com/psf/requests/issues/2505
        # :ref https://github.com/pallets/flask/issues/1384
        # :ref https://github.com/psf/requests/issues/2883
        # :ref https://github.com/psf/requests/issues/2313
        return Response("TODO; Content-Type: multipart/form-data is unsupported", status=415)

        # `request.files` will be a MultiDict object
        # :ref https://werkzeug.palletsprojects.com/en/0.15.x/datastructures/#werkzeug.datastructures.MultiDict

        """
        files = list(request.files.items())
        if len(files) != 1:
            return Response(
                    "POST /index/<piece_id> accepts exactly file at a time "
                    f"but received a multipart/form-data POST with {len(files)} files", status=415)
        else:
            symbolic_data = files[0].read()
            metadata["filename"] = request.form.get("filename", None)
            metadata["collection"] = request.form.get("collection", None)
        """

    elif request.content_type == "application/x-www-form-urlencoded":
        return Response("TODO; Content-Type: application/x-www-form-urlencoded is unsupported", status=415)
    elif request.content_type == "application/octet-stream":
        # Random 16-byte string
        SEPARATOR = unhexlify("90dc2e88fb6b4777432355a4bc7348fd17872e78905a7ec6626fe7b0f10a2e5a")
        try:
            metadata_bytes, symbolic_data = request.data.split(SEPARATOR)
        except ValueError:
            return Response(f"Request is malformed. It must have exactly one occurrence of the following byte string separating the JSON metadata and piece data, and this separator cannot be contained in the data itself: {SEPARATOR}")
        metadata_req = json.loads(metadata_bytes.decode("utf-8"))
        metadata_dict.update(metadata_req)
    else:
        return Response(f"Unsupported Content-Type: {request.content_type}", 415)
    if not symbolic_data:
        return Response("Failed to find piece data in POST request body", status=400)

    try:
        p = piece.Piece(symbolic_data, metadata.Metadata(**metadata_dict))
    except Exception as e:
        return Response(f"failed to parse symbolic data with music21: {str(e)}", status=415)

    logger.info(f"POST /index/<piece_id>: inserting piece of size {len(symbolic_data)} bytes, with metadata {metadata_dict}")

    with db_conn, db_conn.cursor() as cur:
        if piece_id:
            values = (piece_id, base64.b64encode(symbolic_data).decode('utf-8'), metadata_dict['name'], metadata_dict['composer'], metadata_dict['fmt'], metadata_dict['filename'], metadata_dict['collection_id'])
            conflict_values = values[1:]
            cur.execute(f"""
                INSERT INTO Piece (pid, symbolic_data, name, composer, fmt, filename, collection_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT ON CONSTRAINT piece_pkey DO
                UPDATE SET (symbolic_data, name, composer, fmt, filename, collection_id) = (%s, %s, %s, %s, %s, %s)
            ;""", values + conflict_values)
        else:
            values = (base64.b64encode(symbolic_data).decode('utf-8'), metadata_dict['name'], metadata_dict['composer'], metadata_dict['fmt'], metadata_dict['filename'], metadata_dict['collection_id'])
            cur.execute(f"""
                INSERT INTO Piece (symbolic_data, name, composer, fmt, filename, collection_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING pid
            ;""", values)
            piece_id, = cur.fetchone()

    pb_notes = [n.to_pb() for n in p.notes]

    with grpc.insecure_channel(application.config['SMR_URI']) as channel:
        stub = smr_pb2_grpc.SmrStub(channel)
        response = stub.AddPiece(smr_pb2.AddPieceRequest(pid = piece_id, notes = pb_notes))

    return Response(str(piece_id), mimetype='text/plain')


@application.route("/excerpt", methods=["GET"])
def excerpt():
    """
    Returns a highlighted excerpt of a score
    """
    db_conn = connect_to_psql()
    piece_id = int(request.args.get("pid"))
    notes = [str(x) for x in request.args.get("nid").split(",")]

    with db_conn, db_conn.cursor() as cur:
        query = "SELECT colored_excerpt(" + str(piece_id) + ", '{" + request.args.get("nid") + "}', '#FF0000');"
        cur.execute(query)
        excerpt_xml, = cur.fetchone()
    return Response(excerpt_xml, mimetype='text/xml')

@application.route("/search", methods=["GET"])
def search():
    db_conn = connect_to_psql()

    for arg in (x.name for x in fields(QueryArgs)):
        missing = []
        if not request.args.get(arg):
            missing.append(arg)
        if missing:
            return Response(f"Missing GET parameter(s): {missing}", status=400)

    try:
        page = int(request.args.get("page"))
        rpp = int(request.args.get("rpp"))
        tnps = request.args.get("tnps").split(",")
        tnps_ints = list(map(int, tnps))
        tnps_ints[1] += 1 # increase range to include end
        intervening = request.args.get("intervening").split(",")
        intervening_ints = tuple(map(int, intervening))
        inexact = request.args.get("inexact").split(",")
        inexact_ints = tuple(map(int, inexact))
        collection = int(request.args.get("collection"))
        query_str = request.args.get("query")
        qargs = QueryArgs(rpp, page, tnps, intervening, inexact, collection, query_str)
    except ValueError as e:
        return Response(f"Failed to parse parameter(s) to integer, got exception {str(e)}", status=400)

    query_score = indexers.parse(query_str)
    query_pb_notes = indexers.pb_notes(query_score)

    with db_conn.cursor() as cur:
        if collection == 0:
            # all pieces
            cur.execute("SELECT pid FROM Piece;")
        else:
            cur.execute(f"SELECT pid FROM Piece WHERE collection_id={collection}")
        collection_pids = [x[0] for x in cur.fetchall()]

    channel_opts = [
        ('grpc.max_message_length', 1024**3),
        ('grpc.max_receive_message_length', 1024**3)
    ]
    try:
        with grpc.insecure_channel(application.config['SMR_URI'], options=channel_opts) as channel:
            stub = smr_pb2_grpc.SmrStub(channel)
            response = stub.Search(smr_pb2.SearchRequest(notes=query_pb_notes, pids=collection_pids))
    except Exception as e:
        return Response(f"failed to search: {str(e)}", status=500)

    print("smr service returned #" + str(len(response.occurrences)) + " occurrences")
    occfilters = occurrence.OccurrenceFilters(
            transpositions = range(*tnps_ints),
            intervening = intervening_ints,
            inexact = inexact_ints)

    search_response = build_response(
            db_conn,
            occurrence.filter_occurrences(response.occurrences, query_pb_notes, occfilters),
            qargs)

    if request.content_type == "application/json":
        return jsonify(search_response)
    else:
        return render_template("search.html", searchResponse = search_response)

@application.route("/search_sql", methods=["GET"])
def search_sql():
    def qstring(ps):
        return "'{" + ','.join(f'\"({x.onset},{x.pitch})\"' for x in ps) + "}'"
    db_conn = connect_to_psql()

    for arg in (x.name for x in fields(QueryArgs)):
        missing = []
        if not request.args.get(arg):
            missing.append(arg)
        if missing:
            return Response(f"Missing GET parameter(s): {missing}", status=400)

    try:
        page = int(request.args.get("page"))
        rpp = int(request.args.get("rpp"))
        tnps = request.args.get("tnps").split(",")
        tnps_ints = list(map(int, tnps))
        tnps_ints[1] += 1 # increase range to include end
        intervening = request.args.get("intervening").split(",")
        intervening_ints = tuple(map(int, intervening))
        inexact = request.args.get("inexact").split(",")
        inexact_ints = tuple(map(int, inexact))
        collection = int(request.args.get("collection"))
        query_str = request.args.get("query")
        qargs = QueryArgs(rpp, page, tnps, intervening, inexact, collection, query_str)
    except ValueError as e:
        return Response(f"Failed to parse parameter(s) to integer, got exception {str(e)}", status=400)

    query_score = indexers.parse(query_str)
    query_notes = [piece.Note.from_m21(n, i) for i, n in enumerate(indexers.NotePointSet(query_score))]

    print("asking pg to search...")
    with db_conn, db_conn.cursor() as cur:
        cur.execute(f"""
            SELECT pid, nids FROM search_sql({qstring(query_notes)})
            WHERE array_length(nids, 1) >= 5;""")
        occurrences = cur.fetchall()
    print(f"got {len(occurrences)} results")

    search_response = build_sql_response(occurrences, qargs)

    if request.content_type == "application/json":
        return jsonify(search_response)
    else:
        return render_template("search.html", searchResponse = search_response)

def main():
    application.run(host="0.0.0.0", port=int(os.environ['FLASK_PORT']))

if __name__ == '__main__':
    main()
