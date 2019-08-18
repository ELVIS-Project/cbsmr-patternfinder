import os
import multiprocessing
import pytest
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
            params={"query": query_template(q), "rpp": rpp, "page": page, "tnps": "0,1,2,3,4,5,6,7,8,9,10,11", "intervening": 10})
    return response

def assert_search_200(q, rpp, page):
    resp = search(q, rpp, page)
    assert resp.status_code == 200, "searching for {} failed: {}".format(q, resp.content)

def post_piece_from_file(i, p):
    with open(p, "rb") as f:
        status = requests.post(f"{ENDPOINT}/index/{str(i)}", headers={'Content-type': 'application/octet-stream'}, data=f.read()) 
        assert status.status_code == 200, "post failed on {}: {}".format(p, status.content)

def main():
    pdir = os.path.join(PROJROOT, 'tests', 'testdata', 'palestrina_masses', 'mid')
    masses = os.listdir(pdir)

    with multiprocessing.Pool() as p:
        inputs = ((i, os.path.join(pdir, m)) for i, m in enumerate(masses))
        p.starmap_async(post_piece_from_file, inputs)

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
