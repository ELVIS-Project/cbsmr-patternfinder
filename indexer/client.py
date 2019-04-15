# :todo fix paths to proto/
import os
import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'proto'))
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'indexer'))
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'conf'))

import logging
import base64
import grpc

import config
from indexer import server
from proto import smr_pb2, smr_pb2_grpc

def index_notes_oneshot(path):
    s = server.new_server(config.INDEXER_PORT)
    s.start()

    index_notes(f"{config.INDEXER_HOST, config.INDEXER_PORT}", path)

    s.stop(0)

def index_notes(path):
    
    with open(path, 'rb') as f:
        symbolic_data = f.read()

    with grpc.insecure_channel(f"{config.INDEXER_HOST, config.INDEXER_PORT}") as channel:
        stub = smr_pb2_grpc.IndexStub(channel)
        response = stub.IndexNotes(smr_pb2.IndexRequest(symbolic_data = symbolic_data))

    return response

    
if __name__ == '__main__':
    logging.basicConfig()
    response = index_notes(sys.argv[1])

    if len(sys.argv) > 2:
        with open(sys.argv[2], "wb") as f:
            f.write(response.SerializeToString())
    else:
        print(response.notes)
