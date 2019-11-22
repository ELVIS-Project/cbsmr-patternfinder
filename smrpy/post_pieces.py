#!/usr/local/bin/python3

import sys
import os
import multiprocessing
import requests
import json
import base64
import music21
from dataclasses import asdict
from metadata import Metadata
from binascii import unhexlify
from tqdm import tqdm
import psycopg2

ELVISDUMP = "/Users/davidgarfinkle/elvis-project/elvisdump/"
ENDPOINT = os.getenv("HOST") or "localhost:80"
def post_piece_octet_stream(path, endpoint=ENDPOINT):
    md = Metadata.from_path_and_env(path)

    data = b''
    metadata_http = bytes(json.dumps(asdict(md)), encoding="utf-8")
    data += metadata_http
    data += unhexlify("90dc2e88fb6b4777432355a4bc7348fd17872e78905a7ec6626fe7b0f10a2e5a")
    with open(path, 'rb') as f:
        data += f.read()

    endpoint = f"http://{endpoint}/index" + (f"/{str(md.pid)}" if md.pid else "")
    resp = requests.post(endpoint,
                        data=data,
                        headers={'Content-Type': 'application/octet-stream'})
    if resp.status_code != 200:
        print(f"failed to post {path}: {resp.content}")
    else:
        print("OK")

def post_piece_multipart_formdata(path, endpoint=ENDPOINT):
    if os.getenv("PARSE_ELVIS"):
        index, fmt, name = parse_piece_path(path)
        endpoint = f"http://{ENDPOINT}/index/{str(index)}"
    else:
        endpoint = f"http://{ENDPOINT}/index"

    with open(path, 'rb') as f:
        data = f.read()

    resp = requests.post(endpoint,
                        data={
                            "file_name": name,
                            "collection": 1
                        },
                        files={"foo": data},
                        headers={'Content-Type': 'multipart/form-data'})
    if resp.status_code != 200:
        print(f"failed to post {path}: {resp.content}")
    else:
        print("OK")

def insert_piece(path):
    md = Metadata.from_path_and_env(path)
    with open(path, "rb") as f:
        sd = base64.b64encode(f.read()).decode('utf-8')
    conn = psycopg2.connect("")
    with conn.cursor() as cur:
        cur.execute(f"""
            INSERT INTO Piece (pid, fmt, name, composer, symbolic_data, collection_id)
            VALUES (%s, %s, %s, '', %s, %s)""", (md.pid, md.fmt, md.name, sd, md.collection_id)
        )
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("post_pieces.py <path1> <path2> ... <pathn>")
    #with multiprocessing.Pool() as p:
        #p.map(post_piece_octet_stream, sys.argv[1:])
    for p in tqdm(sys.argv[1:]):
        try:
            post_piece_octet_stream(p)
        except Exception as e:
            print(e)
