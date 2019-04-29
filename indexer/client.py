# :todo fix paths to proto/
import os
import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'proto'))
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'indexer'))
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'conf'))

import logging
import base64
import grpc

from indexer import server
from proto import smr_pb2, smr_pb2_grpc

def index_notes_oneshot(pb_req):
    s = server.new_server(os.environ['INDEXER_PORT'])
    s.start()

    index_notes(pb_req)

    s.stop(0)

def index_notes(pb_req):

    with grpc.insecure_channel(f"{os.environ['INDEXER_HOST']}:{os.environ['INDEXER_PORT']}", options = server.OPTIONS) as channel:
        stub = smr_pb2_grpc.IndexStub(channel)
        response = stub.IndexNotes(pb_req)

    return response

def index_notes_from_file(path):
    with open(path, 'rb') as f:
        data = f.read()

    req = smr_pb2.IndexRequest(symbolic_data = data)

    try:
        return index_notes(req)
    except Exception as e:
        return index_notes_oneshot(req)
    
if __name__ == '__main__':
    logging.basicConfig()
    response = index_notes_from_file(sys.argv[1])

    if len(sys.argv) > 2:
        with open(sys.argv[2], "wb") as f:
            f.write(response.SerializeToString())
    else:
        print(response.notes)
