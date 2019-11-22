#!/usr/local/bin/python3
import os
import music21
from flask import Flask, request, jsonify, Response, send_from_directory, render_template
from smrpy.occurrence import filter_occurrences, OccurrenceFilters
from smrpy.hausdorf import generate_normalized_windows_with_notes
from smrpy import occurrence, piece
from smrpy import indexers
from smrpy.metadata import Metadata
import requests
import json
from binascii import unhexlify
from dataclasses import fields

import psycopg2
import time

from smrpy.response import build_response, QueryArgs
from smrpy.excerpt import coloured_excerpt

application = Flask(__name__)
logger = application.logger

POSTGREST_URI = "http://localhost:3000"

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
def favicon():
    return send_from_directory('templates', 'favicon.ico')

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
        p = piece.Piece(symbolic_data, **metadata_dict)
    except music21.Music21Exception as e:
        return Response(f"failed to parse symbolic data with music21: {str(e)}", status=415)

    logger.info(f"POST /index/<piece_id>: inserting piece of size {len(symbolic_data)} bytes, with metadata {metadata_dict}")

    with db_conn, db_conn.cursor() as cur:
        query, _, values = p.insert_str()
        cur.execute(query, values)
        piece_id, = cur.fetchone()

        for n in p.notes:
            query, _, values = n.insert_str(piece_id)
            cur.execute(query, values)

        for (u, v), normalized_window, window in generate_normalized_windows_with_notes(p.notes, 10):
            point_array = "'{" + ','.join(('"(%s, %s)"',) * len(window)) + "}'"
            query = f"INSERT INTO NoteWindow(pid, u, v, normalized, unnormalized) VALUES (%s, %s, %s, {point_array}, {point_array})"
            values = [piece_id, u.index, v.index] + [x for n in normalized_window for x in (n.onset, n.pitch)] + [x for n in window for x in (n.onset, n.pitch)]
            cur.execute(query, values)
            for i, n in enumerate(normalized_window):
                cur.execute("INSERT INTO Posting (n, pid, u, v, nid) VALUES ('(%s, %s)', %s, %s, %s, %s)",
                            (n.onset, n.pitch, piece_id, u.index, v.index, n.index))

    return Response(str(piece_id), mimetype='text/plain')

def qstring(ps):
    return "'{" + ','.join(f'\"({x.onset},{x.pitch})\"' for x in ps) + "}'"

@application.route("/excerpt", methods=["GET"])
def excerpt():
    db_conn = connect_to_psql()
    piece_id = int(request.args.get("pid"))
    notes = [str(x) for x in request.args.get("nid").split(",")]
    excerpt_xml = coloured_excerpt(db_conn, notes, piece_id)
    #excerpt_xml = requests.get("http://localhost:3000/rpc/excerpt", {"pid": piece_id, "nids": '{' + ','.join(notes) + '}'}).content
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

    query_str = request.args.get("query")
    query_stream = indexers.parse(query_str)
    query_nps = indexers.NotePointSet(query_stream)
    query_notes = [(n.offset, n.pitch.ps) for n in query_nps]
    query_pb_notes = [piece.Note(n[0], None, n[1], i).to_pb() for i, n in enumerate(query_notes)]

    with db_conn, db_conn.cursor() as cur:
        cur.execute(f"""
            SELECT * FROM search({qstring(query_pb_notes)})
        """)
        occurrences = [{'pid': pid, 'name': name, 'notes': notes} for pid, name, notes in cur.fetchall()]
    #resp = requests.get(POSTGREST_URI + "/rpc/search", params=('query=' + qstring(query_pb_notes))).json()
    #occurrences = [occurrence.occ_to_occpb(occ) for occ in resp]

    #occfilters = OccurrenceFilters(
    #        transpositions = range(*tnps_ints),
    #        intervening = intervening_ints,
    #        inexact = inexact_ints)

    search_response = build_response(occurrences, qargs)

    if request.content_type == "application/json":
        return jsonify(search_response)
    else:
        return render_template("search.html", searchResponse = search_response)

def main():
    application.run(host="0.0.0.0", port=int(os.getenv('FLASK_PORT', 80)))

if __name__ == '__main__':
    main()
