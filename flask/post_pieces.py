#!/usr/local/bin/python3

import sys
import os
import multiprocessing
import requests
import json
import music21
from dataclasses import dataclass
from binascii import unhexlify

ELVISDUMP = "/Users/davidgarfinkle/elvis-project/elvisdump/"
ENDPOINT = os.getenv("HOST") or "localhost:80"
NUM_PIECES_PER_COLLECTION = 100000

@dataclass
class Metadata:
    index: int
    fmt: str
    name: str
    collection_id: int

def unique_index(i, collection_id):
    base = NUM_PIECES_PER_COLLECTION * collection_id
    return base + i

def parse_kern_chorale_piece_path(piece_path):
    collection_id = 2
    fmt = 'krn'
    basename, _ = os.path.splitext(os.path.basename(piece_path))
    index = int(basename[-3:])
    name = music21.converter.parse(piece_path).metadata.title
    return Metadata(unique_index(index, collection_id), fmt, name, collection_id)

def parse_elvis_piece_path(piece_path):
    collection_id = 1
    basename, fmt = os.path.splitext(os.path.basename(piece_path))
    fmt = fmt[1:] # skip '.'
    base = [x for x in os.path.basename(basename).split("_") if not "file" in x]
    piece_id = int(base[0])
    name = base[1]
    return Metadata(unique_index(piece_id, collection_id), fmt, name, collection_id)

def parse_palestrina_path(piece_path):
    collection_id=3
    fmt = 'mid'
    basename, _ = os.path.splitext(os.path.basename(piece_path))
    xs = basename.split('_')
    name = " ".join(xs[:-2])
    num_voices = xs[-1]
    movement = xs[-2]

    return Metadata(index=None, fmt=fmt, name=f"{name} {movement[0].upper()}{movement[1:]} à {num_voices}", collection_id=collection_id)

def post_piece_octet_stream(path, endpoint=ENDPOINT):
    if os.getenv("PARSE_ELVIS"):
        metadata = parse_elvis_piece_path(path)
        endpoint = f"http://{ENDPOINT}/index/{str(metadata.index)}"
    elif os.getenv("PARSE_CHORALE"):
        metadata = parse_kern_chorale_piece_path(path)
        endpoint = f"http://{ENDPOINT}/index/{str(metadata.index)}"
    elif os.getenv("PARSE_PALESTRINA"):
        metadata = parse_palestrina_path(path)
        print(f"posting to collection {metadata.collection_id} without index arg")
        endpoint = f"http://{ENDPOINT}/index"
    else:
        print("posting to collection 0 without index arg")
        metadata = Metadata(None, path[-3:], path, 0)
        endpoint = f"http://{ENDPOINT}/index"

    data = b''
    metadata_http = bytes(json.dumps({
        "filename": metadata.name,
        "collection": metadata.collection_id,
        "fmt": metadata.fmt
    }), "utf-8")
    data += metadata_http
    data += unhexlify("90dc2e88fb6b4777432355a4bc7348fd17872e78905a7ec6626fe7b0f10a2e5a")
    with open(path, 'rb') as f:
        data += f.read()

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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("post_pieces.py <path1> <path2> ... <pathn>")
    with multiprocessing.Pool() as p:
        p.map(post_piece_octet_stream, sys.argv[1:])
