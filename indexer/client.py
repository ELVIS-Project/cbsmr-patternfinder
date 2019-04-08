# :todo fix paths to proto/
import os
import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'proto'))
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'indexer'))

import logging
import base64
import grpc

from indexer import server

from proto import smr_pb2, smr_pb2_grpc

def index_notes(path):
    
    s = server.new_server()
    s.start()

    with open(path, 'rb') as f:
        symbolic_data = f.read()

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = smr_pb2_grpc.IndexStub(channel)
        response = stub.IndexNotes(smr_pb2.IndexRequest(symbolic_data = symbolic_data))

    s.stop(0)
    return response
    
if __name__ == '__main__':
    logging.basicConfig()
    response = index_notes(sys.argv[1])

    if len(sys.argv) > 2:
        with open(sys.argv[2], "wb") as f:
            f.write(response.SerializeToString())
    else:
        print(response.notes)
