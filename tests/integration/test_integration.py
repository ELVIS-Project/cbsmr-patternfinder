import pytest
import os
import requests

FLASK_URI = "http://localhost:80"

double_leading_tone_query = """**kern
*clefG2
*k[]
*M4/4
=-
4c 4e 4a 4cc
4B- f b- dd
"""

def search(q):
    status = requests.get(f"{FLASK_URI}/search", params={"query": q, "rpp": 5, "page": 0})
    assert status.status_code == 200, "searching for {} failed: {}".format(q, status.content)

def post_piece(i, p):
    with open(p, "rb") as f:
        status = requests.post(f"{FLASK_URI}/index/{str(i)}", headers={'Content-type': 'application/octet-stream'}, data=f.read()) 
        assert status.status_code == 200, "post failed on {}: {}".format(p, status.content)

def post_masses():
    pdir = "tests/testdata/palestrina_masses/mid"
    masses = os.listdir(pdir)

    for i, mass in enumerate(masses):
        mpath = os.path.join(pdir, mass)
        post_piece(i, mpath)

def test_lemstrom():
    pdir = "tests/testdata/lemstrom2011/"
    queries = (f"query_{t}.mid" for t in ("a", "b", "c", "d", "e", "f"))
    post_piece(0, pdir + "leiermann.xml")

def search_double_leading_tone():
    status = requests.get(f"{FLASK_URI}/search", params={"query": double_leading_tone_query, "rpp": 5, "page": 0})
    assert status.status_code == 200, "search failed: {}".format(status.content)

def test_palestrina_masses():
    post_masses()
    search_double_leading_tone()