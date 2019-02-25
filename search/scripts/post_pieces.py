import os
import requests
import base64
import psycopg2
import indexers
from tqdm import tqdm
from _w2 import ffi, lib


ELVISDUMP = "/Users/davidgarfinkle/elvis-project/elvisdump"
ENDPOINT = "http://localhost:5000/"

"""
POSTGRES_CONN_STR = 'host=localhost dbname=postgres user=postgres password=postgres'
CONN = psycopg2.connect(POSTGRES_CONN_STR)
CONN.autocommit = True
"""

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
        for p in tqdm(files):
            response = post_piece(p)
            f.write(f"p {p}, resp {response.content}\n")


def index_one():
    p = "/Users/davidgarfinkle/elvis-project/elvisdump/MID/000000000003688_Virgo-salutifieri-genitrix_Josquin-Des-Prez_file4.midi"
    response = post_piece(p)
    from pprint import pprint
    pprint(response.content.decode('utf-8'))

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

    result = lib.search(query_csv.encode('utf-8'), target_csv.encode('utf-8'))

    return result

def search_lemstrom():

    with open("helsinki-ttwi/tests/query_a.vectors", "r") as f:
        q_str = f.read()

    with open("helsinki-ttwi/tests/leiermann.vectors" , "r") as f:
        t_str = f.read()

    
    res = ffi.new("struct Result*")

    result = lib.search_return_chains(q_str.encode('utf-8'), t_str.encode('utf-8'), res)

    return res
