# :todo fix paths to proto/
import os
import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'proto'))

import logging

import grpc

import types_pb2
import indexer_pb2
import indexer_pb2_grpc


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = indexer_pb2_grpc.IndexerStub(channel)
        response = stub.IndexPiece(indexer_pb2.IndexRequest(type=indexer_pb2.NOTE))
    print("Greeter client received: " + str(response.measures))


if __name__ == '__main__':
    logging.basicConfig()
run()