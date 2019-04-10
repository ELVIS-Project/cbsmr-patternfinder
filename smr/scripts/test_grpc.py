import os
import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, os.pardir, 'proto'))

import grpc
import base64
import smr_pb2, smr_pb2_grpc


TP = [
    (2678, "000000000002678_Sancta-mater-istud-agas_Penalosa-Francisco_file5.mei"),
    (10113, "000000000010113_Sonata-in-G-minor-Op.-4-No.-2_Grave_Corelli-Arcangelo_file1.xml"),
    (10138, "000000000010138_Je-me-recommande_Binchois-Gilles-de-Bins-dit_file1.xml"),
    (2557, "000000000002557_Regina-caeli-letare_Josquin-Des-Prez_file5.mei"),
    (11125, "palestrina_masses/000000000011125_Missa-Hodie-christus-natus-est_Sanctus_Palestrina-Giovanni-Pierluigi-da_file2.mid"),
    (11344, "palestrina_masses/000000000011344_Missa-Primi-toni_Credo_Palestrina-Giovanni-Pierluigi-da_file2.mid")
]

def add_piece(i, path):
    smr_channel = grpc.insecure_channel("localhost:8080").__enter__()
    index_channel = grpc.insecure_channel("localhost:50051").__enter__()
    smr = smr_pb2_grpc.SmrStub(smr_channel)
    index = smr_pb2_grpc.IndexStub(index_channel)

    with open("/Users/davidgarfinkle/elvis-project/cbsmr-patterfinder/smr/testdata/" + path, "rb") as f:
        sd = f.read()

    pb_notes = index.IndexNotes(smr_pb2.IndexRequest(
        encoding = smr_pb2.IndexRequest.BASE64,
        symbolic_data = base64.b64encode(sd)))
    smr.AddPiece(smr_pb2.AddPieceRequest(id=i, notes=pb_notes))


    smr_channel.__exit__(*sys.exc_info())
    index_channel.__exit__(*sys.exc_info())

def add_pieces():
    for i, piece in TP:
        try:
            add_piece(i, piece)
        except Exception as e:
            print(piece + " failed")
            print(e)


def search_grpc():
    query_str = """**kern
        *clefG2
        *k[]
        *M4/4
        =-
        4c 4e 4a 4cc
        4B- f b- dd
        """
    with grpc.insecure_channel("localhost:8080") as smr_channel, grpc.insecure_channel("localhost:50051") as index_channel:
        smr = smr_pb2_grpc.SmrStub(smr_channel)
        index = smr_pb2_grpc.IndexStub(index_channel)

        pb_notes = index.IndexNotes(smr_pb2.IndexRequest(symbolic_data = bytes(query_str, encoding='utf-8'), encoding = smr_pb2.IndexRequest.UTF8))
        result = smr.Search(pb_notes)

        print(result)
    
"""
"""

