import os
import base64
import pytest
import requests

ENDPOINT = f"http://{os.environ['FLASK_HOST']}:{os.environ['FLASK_PORT']}/"

def test_root_conn():
    assert requests.get(ENDPOINT).status_code == 200

def test_index():

    # MEI indexing is broken
    #path = "../tests/testdata/000000000002557_Regina-caeli-letare_Josquin-Des-Prez_file5.mei"

    path = "../tests/testdata/000000000010113_Sonata-in-G-minor-Op.-4-No.-2_Grave_Corelli-Arcangelo_file1.xml"
    with open(path, 'r') as f:
        dumpname, fmt = os.path.splitext(os.path.basename(path))
        index, _, name = dumpname.partition('_')
        with open(path, 'rb') as f:
            data = f.read()

        resp = requests.post(ENDPOINT + "index/" + str(index),
                            data=data,
                            headers={'Content-Type': 'application/octet-stream'})

    assert resp.status_code == 200, "Index request failed; response\n" + str(resp.content)

def test_excerpt():
    resp = requests.get(ENDPOINT + "excerpt", params={'nid': '1,3,5', 'pid': '10113'})
    assert resp.status_code == 200

def test_search():
    query_str = """**kern
        *clefG2
        *k[]
        *M4/4
        =-
        4c 4e 4a 4cc
        4B- f b- dd"""
    resp = requests.get(ENDPOINT + "search",
            params={'query': query_str, 'rpp': 5, 'page': 0})

    assert resp.status_code == 200
