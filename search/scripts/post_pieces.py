import os
import requests
import base64

ENDPOINT = "http://localhost:5000/"

def post_piece(path):
    dumpname, format = os.path.splitext(os.path.basename(path))
    index, _, name = dumpname.partition('_')

    with open(path, 'rb') as f:
        data = base64.b64encode(f.read())

    return requests.post(ENDPOINT + "index/" + str(index),
                        data=data,
                        headers={'Content-Type': 'application/octet-stream'})

