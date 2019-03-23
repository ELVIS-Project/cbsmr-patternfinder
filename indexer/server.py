# :todo fix paths to proto/
import os
import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'proto'))

from concurrent import futures
import time
import logging

import grpc

import types_pb2
import indexer_pb2
import indexer_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class Indexer(indexer_pb2_grpc.IndexerServicer):

    def IndexPiece(self, request, context):
        return indexer_pb2.IndexResponse(measures=[types_pb2.Measure(symbolicData=b'', number=5)])

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    indexer_pb2_grpc.add_IndexerServicer_to_server(Indexer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    logging.basicConfig()
serve()