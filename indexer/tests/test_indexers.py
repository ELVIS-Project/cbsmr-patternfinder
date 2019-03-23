
# :todo fix paths to proto/
import os
import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'proto'))

import pytest
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

"""
import pkg_resources
import indexers
import pandas as pd

def test_notes():
    with pkg_resources.resource_stream("indexers", "tests/leiermann.xml") as f:
        symbolic_data = f.read()

    with pkg_resources.resource_stream("indexers", "tests/leiermann.notes") as f:
        notes_expected = pd.read_csv(f)
    
    notes_actual = indexers.notes(symbolic_data)

    assert notes_actual.equals(notes_expected)

def test_intra_vectors():
    with pkg_resources.resource_stream("indexers", "tests/leiermann.xml") as f:
        symbolic_data = f.read()

    with pkg_resources.resource_stream("indexers", "tests/leiermann.intra_vectors") as f:
        intra_vectors_expected = pd.read_csv(f)
    
    intra_vectors_actual = indexers.intra_vectors(symbolic_data)

    assert intra_vectors_actual.equals(intra_vectors_expected)
"""