#!/usr/local/bin/python3

import sys
import os
import multiprocessing
import requests
import json
import music21
from dataclasses import asdict
from binascii import unhexlify
from smrpy import metadata

ELVISDUMP = "/Users/davidgarfinkle/elvis-project/elvisdump/"
ENDPOINT = os.getenv("HOST")

def post_piece_octet_stream(path, endpoint=ENDPOINT):
    md = metadata.Metadata.from_path_and_env(path)

    data = b''
    metadata_http = bytes(json.dumps(asdict(md)), encoding="utf-8")
    data += metadata_http
    data += unhexlify("90dc2e88fb6b4777432355a4bc7348fd17872e78905a7ec6626fe7b0f10a2e5a")
    with open(path, 'rb') as f:
        data += f.read()

    endpoint = f"{endpoint}/index" + (f"/{str(md.pid)}" if md.pid else "")
    resp = requests.post(endpoint,
                        data=data,
                        headers={'Content-Type': 'application/octet-stream'})
    if resp.status_code != 200:
        print(f"failed to post {path}: {resp.content}")
    else:
        print("OK")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("post_pieces.py <path1> <path2> ... <pathn>")
    with multiprocessing.Pool() as p:
        p.map(post_piece_octet_stream, sys.argv[1:])
