import sys
import requests
from pprint import pprint

ENDPOINT = "http://localhost:80/"

def post_piece(path, index, endpoint=ENDPOINT):

    with open(path, 'rb') as f:
        data = f.read()

    return requests.post(endpoint + "index/" + str(index),
                        data=data,
                        headers={'Content-Type': 'application/octet-stream'})

def search(query, rpp, page):
    return requests.get(ENDPOINT + "search",
            params={'query': query, 'rpp': rpp, 'page': page})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("post_pieces.py <path>")
    post_piece(sys.argv[1])
