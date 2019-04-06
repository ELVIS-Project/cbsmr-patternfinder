import os
import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, os.pardir, 'proto'))

import pytest
import base64
import grpc
import smr_pb2, smr_pb2_grpc

from indexer import server

# Will fail by GRPC check: must pass in bytes to IndexRequest.symbolic_data
with open("./tests/leiermann.xml", "r") as f:
    leiermann_str = f.read()

with open("./tests/leiermann.xml", "rb") as f:
    leiermann_bytes = f.read()

with open("./tests/leiermann.xml", "rb") as f:
    leiermann_base64 = base64.b64encode(f.read())

with open("./tests/leiermann.pb_notes", "rb") as f:
    leiermann_expected_pb_notes = f.read()

# Will fail by GRPC check: must pass in bytes to IndexRequest.symbolic_data
krn_str = """**kern
    *clefG2
    *k[]
    *M4/4
    =-
    4c 4e 4a 4cc
    4B- f b- dd"""

krn_utf8 = bytes("""**kern
    *clefG2
    *k[]
    *M4/4
    =-
    4c 4e 4a 4cc
    4B- f b- dd""", encoding='utf-8')

def test_index_notes():

    s = server.new_server()
    s.start()

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = smr_pb2_grpc.IndexStub(channel)

        response = stub.IndexNotes(smr_pb2.IndexRequest(symbolic_data = leiermann_bytes))
        assert(response.SerializeToString() == leiermann_expected_pb_notes)

        response = stub.IndexNotes(smr_pb2.IndexRequest(
            symbolic_data = leiermann_base64,
            encoding = smr_pb2.IndexRequest.BASE64))
        assert(response.SerializeToString() == leiermann_expected_pb_notes)

        response = stub.IndexNotes(smr_pb2.IndexRequest(symbolic_data = krn_utf8))
         
    s.stop(0)

"""
import pkg_resources
def test_notes():
    with pkg_resources.resource_stream("indexers", "tests/leiermann.xml") as f:
        symbolic_data = f.read()
"""
