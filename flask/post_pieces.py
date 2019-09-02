#!/usr/local/bin/python3

import sys
import os
import multiprocessing
import requests
import base64
import psycopg2
import json
import music21
from tqdm import tqdm
from binascii import unhexlify


ELVISDUMP = "/Users/davidgarfinkle/elvis-project/elvisdump/"
ENDPOINT = os.getenv("HOST") or "localhost:80"

"""
POSTGRES_CONN_STR = 'host=localhost dbname=postgres user=postgres password=postgres'
CONN = psycopg2.connect(POSTGRES_CONN_STR)
CONN.autocommit = True

xml_pieces = (os.path.join(ELVISDUMP, "XML", f) for f in os.listdir(os.path.join(ELVISDUMP, "XML")))
mid_pieces = (os.path.join(ELVISDUMP, "MID", f) for f in os.listdir(os.path.join(ELVISDUMP, "MID")))
mei_pieces = (os.path.join(ELVISDUMP, "MEI", f) for f in os.listdir(os.path.join(ELVISDUMP, "MEI")))
"""

def parse_piece_path(piece_path):
    basename, fmt = os.path.splitext(os.path.basename(piece_path))
    fmt = fmt[1:] # skip '.'
    base = [x for x in os.path.basename(basename).split("_") if not "file" in x]

    piece_id = base[0]
    name = base[1]

    return piece_id, fmt, name

def post_piece_octet_stream(path, endpoint=ENDPOINT):
    if os.getenv("PARSE_ELVIS"):
        index, fmt, name = parse_piece_path(path)
        endpoint = f"http://{ENDPOINT}/index/{str(index)}"
    else:
        endpoint = f"http://{ENDPOINT}/index"

    data = b''
    metadata = bytes(json.dumps({
        "filename": name,
        "collection": 2
    }), "utf-8")
    data += metadata
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

def search_grpc():
    query_str = """**kern
        *clefG2
        *k[]
        *M4/4
        =-
        4c 4e 4a 4cc
        4B- f b- dd"""
    return requests.get(ENDPOINT + "search",
            params={'query': query_str, 'rpp': 5, 'page': 0})


def index_all():
    files = []

    for subdir in ("MEI", "XML", "MID"):
        directory = os.path.join(ELVISDUMP, subdir)

    for fl in os.listdir(directory):
        filepath = os.path.abspath(os.path.join(directory, fl))
        files.append(filepath)

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "post_piece.log"), "w", buffering=1) as f:
        for p in tqdm(files[:95]):
            response = post_piece(p)
            f.write(f"p {p}, resp {response.content}\n")


def index_one(path=None):
    p = path or "000000000011007_Missa-Io-mi-son-giovinetta-primi-toni-_Credo_Palestrina-Giovanni-Pierluigi-da_file2.mid"
    response = post_piece(ELVISDUMP + 'MID/' + p)
    from pprint import pprint
    pprint(response.content.decode('utf-8'))

def get_search(query):
    if not query:
        query = """**kern
            *clefG2
            *k[]
            *M4/4
            =-
            4c
            4e
            4g
            4a"""
        
    return requests.get(ENDPOINT + "search", params={'query': query})
    

def search():
    query_str = """**kern
        *clefG2
        *k[]
        *M4/4
        =-
        4c 4e 4a 4cc
        4B- f b- dd"""
    
    res = post_search(query_str)

    for chain, measures in zip(*json.loads(res.content.decode('utf-8')).values()):
        print("Found these note indices: ")
        print(chain)
        for measure in measures:
            print("corresponding to these measures")
            print(base64.b64decode(measure.encode('utf-8')).decode('utf-8'))

    return res


def search_lemstrom():

    with open("helsinki-ttwi/tests/query_a.vectors", "r") as f:
        q_str = f.read()
        q = lib.init_score(q_str.encode('utf-8'))

    with open("helsinki-ttwi/tests/leiermann.vectors" , "r") as f:
        t_str = f.read()
        t = lib.init_score(t_str.encode('utf-8'))

    
    res = ffi.new("struct Result*")

    lib.search_return_chains(q, t, res)

    return legacy.extract_chains(res.table, t.num_notes)

def res_to_measures(res):
    list_of_measures = res.json()['measures']
    return [[base64.b64decode(m).decode('utf-8') for m in sublist] for sublist in list_of_measures]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("post_pieces.py <path1> <path2> ... <pathn>")
    print(sys.argv)
    with multiprocessing.Pool() as p:
        p.map(post_piece_octet_stream, sys.argv[1:])
