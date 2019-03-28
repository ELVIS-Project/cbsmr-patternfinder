# :todo fix paths to proto/
import os
import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'proto'))
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'indexer'))

import logging
import base64

import grpc

from proto import smr_pb2, smr_pb2_grpc

def index_piece(path, name, fmt):
    with open(path, 'rb') as f:
        symbolic_data = f.read()

    pb_piece = smr_pb2.Piece(
        symbolicData = symbolic_data,
        encoding = fmt,
        name = name
    )

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = smr_pb2_grpc.IndexerStub(channel)
        response = stub.IndexPiece(smr_pb2.IndexRequest(piece=pb_piece))

    return response
    
if __name__ == '__main__':
    logging.basicConfig()
    response = index_piece(sys.argv[1])

    print(response.notes)
    print(base64.b64decode(response.measures[0].symbolicData).decode('utf-8'))
