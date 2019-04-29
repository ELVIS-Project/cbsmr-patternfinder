import sys
import os
import psycopg2
import grpc
from indexer import client
from tqdm import tqdm
from proto import smr_pb2, smr_pb2_grpc

indexer_uri = f"{os.environ['INDEXER_HOST']}:{os.environ['INDEXER_PORT']}"
smr_uri = f"{os.environ['SMR_HOST']}:{os.environ['SMR_PORT']}"
conn = psycopg2.connect(f"dbname={os.environ['PG_DB']} user={os.environ['PG_USER']} password={os.environ['PG_PASS']} port={os.environ['PG_PORT']} host={os.environ['PG_HOST']}")

def add_piece(i, b64_data):
    smr_channel = grpc.insecure_channel(smr_uri).__enter__()
    index_channel = grpc.insecure_channel(indexer_uri).__enter__()
    smr = smr_pb2_grpc.SmrStub(smr_channel)
    index = smr_pb2_grpc.IndexStub(index_channel)


    pb_req = smr_pb2.IndexRequest(
        encoding = smr_pb2.IndexRequest.BASE64,
        symbolic_data = bytes(b64_data, encoding='utf-8'))
    pb_notes = client.index_notes(pb_req)

    resp = smr.AddPiece(smr_pb2.AddPieceRequest(id=i, notes=pb_notes))
    print(resp)

    smr_channel.__exit__(*sys.exc_info())
    index_channel.__exit__(*sys.exc_info())

def add_all():
    print("Querying smr")
    with grpc.insecure_channel(smr_uri) as channel:
        stub = smr_pb2_grpc.SmrStub(channel)
        already_existing = stub.AllPieces(smr_pb2.AllPiecesRequest())
    print(str(len(already_existing.pids)) + " scores already in smr")

    print("Querying postgres")
    with conn, conn.cursor() as cur:
        cur.execute("""
            SELECT pid, data
            FROM Piece""")

        print("inserting " + str(cur.rowcount - len(already_existing.pids)) + " pieces to smr")
        result = cur.fetchone()
        while result:
            i, data = result
            if i not in already_existing.pids:
                try: 
                    add_piece(i, data)
                except Exception:
                    print(str(i) + " failed")
            result = cur.fetchone()

if __name__ == '__main__':
    add_all()

