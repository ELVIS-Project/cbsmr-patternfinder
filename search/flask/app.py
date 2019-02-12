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
        data = base64.b64decode(data).decode('utf-8')
        try:
            notes = indexers.notes(data)
            intra_vectors = indexers.intra_vectors(data)
        except Exception as e:
            raise IndexerError from e

        failures = { key: False for key in ("piece", "notes", "intra_vectors") }
        with CONN, CONN.cursor() as cur:
            try:
                cur.execute(
                    f"""
                    INSERT INTO music.pieces (id, name, format, diskpath)
                    VALUES ({piece_id}, '', '', '')
                    """
                )
            except Exception as e:
                failures['piece'] = True
            try:
                cur.execute(indexers.notes_to_sql(notes, piece_id))
            except Exception as e:
                failures['notes'] = True
            try:
                cur.execute(indexers.intra_vectors_to_sql(intra_vectors, piece_id))
            except Exception as e:
                failures['intra_vectors'] = True
    if sum(failures.values()) == 0:
        return "Success!", 200
    else:
        return str(failures), 600
        

if __name__ == '__main__':
    app.run()