from flask import Flask, request
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

CONN = psycopg2.connect(POSTGRES_CONN_STR)
CONN.autocommit = True

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

@app.route("/index/<piece_id>", methods=["GET", "POST"])
def index_id(piece_id):
    """
    Indexes a piece and stores it at :param id
    """
    piece_id = int(piece_id)
    if request.method == "POST":
        data = request.get_data()
        #data = base64.b64decode(data).decode('utf-8')
        try:
            notes = indexers.notes(data)
            legacy_intra_vectors = indexers.legacy_intra_vectors(data, 15)
        except Exception as e:
            raise IndexerError from e

        failures = { key: (False, "") for key in ("piece", "notes", "legacy_intra_vectors") }
        with CONN, CONN.cursor() as cur:
            csv_vectors = indexers.legacy_intra_vectors_to_csv(legacy_intra_vectors)
            cur.execute(
                f"""
                INSERT INTO music.pieces (id, name, vectors, num_notes, format, diskpath)
                VALUES ({piece_id}, '', '{csv_vectors}', '{len(notes.index)}', '', '');
                """
            )
    return "yay!", 200
        
@app.route("/search", methods=["GET"])
def search_all():
    """
    Searches entire database for the query string
    """
    query_str = request.args.get("query")

    df = indexers.legacy_intra_vectors(query_str, 1)
    query_csv = indexers.legacy_intra_vectors_to_csv(df)

    with CONN, CONN.cursor() as cur:
        cur.execute(f"SELECT vectors, id FROM music.pieces")
        target_csv_list = cur.fetchall()

    chains = []
    for target in target_csv_list:
        print(target[1])
        res = ffi.new("struct Result*")
        result = lib.search_return_chains(query_csv.encode('utf-8'), target[0].encode('utf-8'), res)
        chains.append(res.num_occs)

    return str(sum(chains)), 200


if __name__ == '__main__':
    app.run()