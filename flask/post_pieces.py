import sys
import os
import requests
import base64
import psycopg2
import json
import music21
from indexer import indexers
from tqdm import tqdm


ELVISDUMP = "/Users/davidgarfinkle/elvis-project/elvisdump/"
ENDPOINT = "http://localhost:80/"

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

def post_piece(path, endpoint=ENDPOINT):
    index, fmt, name = parse_piece_path(path)

    with open(path, 'rb') as f:
        data = f.read()

    return requests.post(endpoint + "index/" + str(index),
                        data=data,
                        headers={'Content-Type': 'application/octet-stream'})

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


"""
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

"""
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

def search_one():
    p = "000000000011007_Missa-Io-mi-son-giovinetta-primi-toni-_Credo_Palestrina-Giovanni-Pierluigi-da_file2.mid"

    query_str = """**kern
        *clefG2
        *k[]
        *M4/4
        =-
        4c 4e"""
    df = indexers.legacy_intra_vectors(query_str, 1)
    query_csv = indexers.legacy_intra_vectors_to_csv(df)
    query = lib.init_score(query_csv.encode('utf-8'))

    with open(os.path.join(ELVISDUMP, "MID", p), "rb") as f:
        data = f.read()
        df = indexers.legacy_intra_vectors(data, 15)
        target_csv = indexers.legacy_intra_vectors_to_csv(df)
        target = lib.init_score(target_csv.encode('utf-8'))

    res = ffi.new("struct Result*")

    lib.search_return_chains(query, target, res)

    chains = legacy.extract_chains(res.table, target.num_notes)

    return chains

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
        cur.execute("SELECT * FROM index.legacy_intra_vectors WHERE piece_id = {} ORDER BY y".format(pid))
        target_tuple = cur.fetchall()
        vec_count = str(cur.rowcount)
        cur.execute("SELECT * FROM index.notes WHERE piece_id = {}".format(pid))
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
"""


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

def coloured_excerpt(note_list, piece_id):
    excerpt = music21.stream.Stream()
    score_note_ids = []

    with CONN, CONN.cursor() as cur:
        cur.execute(f"SELECT data, nid FROM Measure WHERE pid={piece_id} AND nid BETWEEN {note_list[0]} AND {note_list[-1]}")
        results = cur.fetchall()

    for measure_data, nid in results:
        measure = music21.converter.parse(base64.b64decode(measure_data))
        excerpt.append(measure)

        nps = list(indexers.NotePointSet(measure))
        note_list_from_measure_start = [n - nid for n in note_list if n - nid > 0]
        score_note_ids.extend([nps[i].original_note_id for i in note_list_from_measure_start])
        
    for note in excerpt.flat.notes:
        if note.id in score_note_ids:
            note.style.color = 'red'
    
    excerpt_out = excerpt.write('xml')
    with open(excerpt_out, 'rb') as f:
        excerpt_encoded = base64.b64encode(f.read()).decode('utf-8')

    return excerpt_encoded
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("post_pieces.py <path>")
    post_piece(sys.argv[1])
