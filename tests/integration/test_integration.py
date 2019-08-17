import pytest
import os
import requests

PROJROOT = os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, os.pardir)

ENDPOINT = f"http://{os.getenv('NGINX_HOST')}"

def query_template(q): 
    return f"""**kern
    *clefG2
    *k[]
    *M4/4
    =-
    {q}"""

def search(q, rpp, page):
    response = requests.get(
            f"{ENDPOINT}/search",
            params={"query": query_template(q), "rpp": rpp, "page": page})
    return response

def assert_search_200(q, rpp, page):
    resp = search(q, rpp, page)
    assert resp.status_code == 200, "searching for {} failed: {}".format(q, status.content)

def post_piece_from_file(i, p):
    with open(p, "rb") as f:
        status = requests.post(f"{ENDPOINT}/index/{str(i)}", headers={'Content-type': 'application/octet-stream'}, data=f.read()) 
        assert status.status_code == 200, "post failed on {}: {}".format(p, status.content)

def main():
    pdir = os.path.join(PROJROOT, 'tests', 'testdata', 'palestrina_masses', 'mid')
    masses = os.listdir(pdir)

    for i, mass in enumerate(masses):
        mpath = os.path.join(pdir, mass)
        post_piece_from_file(i, mpath)

    assert_search_200("""
        4c 4e 4a 4cc
        4B- f b-- dd""", rpp=5, page=0)

    assert_search_200("""
        4c 4g
        4d 4a
        4e 4b
        4f 4cc""", rpp=5, page=0)

    assert_search_200("""
        4c 4g
        4d 4a
        4e 4b
        4f 4cc""", rpp=5, page=2)

if __name__ == '__main__':
    main()
