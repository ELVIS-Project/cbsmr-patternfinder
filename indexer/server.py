# :todo fix paths to proto/
import os
import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'proto'))

from concurrent import futures
import time
import logging
import base64

import grpc

from indexer import indexers
from proto import smr_pb2, smr_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class Indexer(smr_pb2_grpc.IndexerServicer):

    def IndexPiece(self, request, context):
        sd = request.piece.symbolicData

        print(f"Indexing piece {request.piece.name}")
        notes = indexers.notes(sd)[['onset', 'offset', 'pitch-b40']]
        pb_notes = [
            smr_pb2.Note(
                onset=on,
                offset=off,
                pitchB40=p,
                pieceIdx=idx)
                for idx, (_, on, off, p) in enumerate(notes.itertuples())]

        measures = indexers.index_measures(sd)
        pb_measures = [
            smr_pb2.Measure(
                symbolicData = data,
                number = num,
                noteIdx = idx)
                for data, num, idx in measures]

        response = smr_pb2.IndexResponse(notes=pb_notes, measures=pb_measures)
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    smr_pb2_grpc.add_IndexerServicer_to_server(Indexer(), server)
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
