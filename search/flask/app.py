from flask import Flask, request
from errors import *
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
            try:
                cur.execute(
                    f"""
                    INSERT INTO music.pieces (id, name, format, diskpath)
                    VALUES ({piece_id}, '', '', '')
                    """
                )
            except Exception as e:
                failures['piece'] = (True, str(e))
            try:
                cur.execute(indexers.notes_to_sql(notes, piece_id))
            except Exception as e:
                failures['notes'] = (True, str(e))
            try:
                cur.execute(indexers.legacy_intra_vectors_to_sql(legacy_intra_vectors, piece_id))
            except Exception as e:
                failures['legacy_intra_vectors'] = (True, str(e))
    if sum(b for b, _ in failures.values()) == 0:
        return "Success!", 200
    else:
        return str(failures), 600
        
@app.route("/search/<piece_id>", methods=["GET"])
def search_one(piece_id):
    """
    Searches database for the query string
    """
    query_str = request.args("query")

    df = indexers.legacy_intra_vectors(query_str, 1)
    query_csv = indexers.legacy_intra_vectors_to_csv(df)




if __name__ == '__main__':
    app.run()