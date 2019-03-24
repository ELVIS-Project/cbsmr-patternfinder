# :todo fix paths to proto/
import os
import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'proto'))

import logging
import base64

import grpc

import types_pb2
import indexer_pb2
import indexer_pb2_grpc

def index_piece(path, name, encoding):
    with open(path, 'rb') as f:
        symbolic_data = f.read()

    pb_piece = types_pb2.Piece(
        symbolicData = symbolic_data,
        encoding = encoding,
        name = name
    )

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = indexer_pb2_grpc.IndexerStub(channel)
        response = stub.IndexPiece(indexer_pb2.IndexRequest(piece=pb_piece))

    return response
    
if __name__ == '__main__':
    logging.basicConfig()
    response = index_piece(sys.argv[1])

    print(response.notes)
    print(base64.b64decode(response.measures[0].symbolicData).decode('utf-8'))