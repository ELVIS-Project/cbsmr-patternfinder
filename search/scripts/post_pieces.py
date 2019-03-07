import os
import requests
import base64
import psycopg2
import indexers
import json
from tqdm import tqdm
from _w2 import ffi, lib


ELVISDUMP = "/Users/davidgarfinkle/elvis-project/elvisdump/"
ENDPOINT = "http://localhost:5000/"

POSTGRES_CONN_STR = 'host=localhost dbname=postgres user=postgres password=postgres'
CONN = psycopg2.connect(POSTGRES_CONN_STR)
CONN.autocommit = True

def post_piece(path):
    dumpname, format = os.path.splitext(os.path.basename(path))
    index, _, name = dumpname.partition('_')

    with open(path, 'rb') as f:
        data = f.read()

    return requests.post(ENDPOINT + "index/" + str(index),
                        data=data,
                        headers={'Content-Type': 'application/octet-stream'})


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

def post_search(query):
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

def search_one():
    p = "000000000011007_Missa-Io-mi-son-giovinetta-primi-toni-_Credo_Palestrina-Giovanni-Pierluigi-da_file2.mid"

    query_str = """**kern
        *clefG2
        *k[]
        *M4/4
        =-
        4c 4e 4a 4cc
        4B- f b- dd"""
    df = indexers.legacy_intra_vectors(query_str, 1)
    query_csv = indexers.legacy_intra_vectors_to_csv(df)

    with open(os.path.join(ELVISDUMP, "MID", p), "rb") as f:
        data = f.read()
        df = indexers.legacy_intra_vectors(data, 15)
        target_csv = indexers.legacy_intra_vectors_to_csv(df)

    res = ffi.new("struct Result*")

    result = lib.search_return_chains(query_csv.encode('utf-8'), target_csv.encode('utf-8'), res)

    assert res.num_occs > 0

    return res

def search_one_db():
    p = "000000000011007_Missa-Io-mi-son-giovinetta-primi-toni-_Credo_Palestrina-Giovanni-Pierluigi-da_file2.mid"
    pid = 11007

    query_str = """**kern
        *clefG2
        *k[]
        *M4/4
        =-
        4c 4e 4a 4cc
        4B- f b- dd"""
    df = indexers.legacy_intra_vectors(query_str, 1)
    query_csv = indexers.legacy_intra_vectors_to_csv(df)

    print("selecting vecs and notes from db...")
    with CONN, CONN.cursor() as cur:
        cur.execute(f"SELECT * FROM index.legacy_intra_vectors WHERE piece_id = {pid} ORDER BY y")
        target_tuple = cur.fetchall()
        vec_count = str(cur.rowcount)
        cur.execute(f"SELECT * FROM index.notes WHERE piece_id = {pid}")
        note_count = str(cur.rowcount)

    print("constructing csv...")
    target_csv = "\n".join(["empty_headers", note_count, vec_count])
    for _, _, a, b, c, d, e, f, g, h in target_tuple:
        target_csv += "\n"
        target_csv += ",".join([str(x) for x in [a, b, c, d, e, f, g, h]])

    res = ffi.new("struct Result*")

    result = lib.search_return_chains(query_csv.encode('utf-8'), target_csv.encode('utf-8'), res)

    assert res.num_occs > 0
    # TODO: make an sql to Struct* Score function so you can store the data structure in mem

    return res


def search_lemstrom():

    with open("helsinki-ttwi/tests/query_a.vectors", "r") as f:
        q_str = f.read()

    with open("helsinki-ttwi/tests/leiermann.vectors" , "r") as f:
        t_str = f.read()

    
    res = ffi.new("struct Result*")

    result = lib.search_return_chains(q_str.encode('utf-8'), t_str.encode('utf-8'), res)

    return res

def res_to_measures(res):
    list_of_measures = res.json()['measures']
    return [[base64.b64decode(m).decode('utf-8') for m in sublist] for sublist in list_of_measures]
