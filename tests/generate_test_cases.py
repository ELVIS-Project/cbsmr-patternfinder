import sys
import os
from indexer import client
from proto import smr_pb2, smr_pb2_grpc

CURDIR = os.path.abspath(os.path.dirname(__file__))
TESTDATA = os.path.join(CURDIR, "testdata")
PALESTRINA = os.path.join(TESTDATA, "palestrina_masses")
LEMSTROM = os.path.join(TESTDATA, "lemstrom2011")
QUERIES = os.path.join(TESTDATA, "queries")

def palestrina():
    midi_dir = os.path.join(PALESTRINA, "mid")
    output_dir = os.path.join(PALESTRINA, "pb_notes")
    for midi_file in os.listdir(midi_dir):
        midi_file_path = os.path.join(midi_dir, midi_file)
        client.index_notes_write_response(midi_file_path, output_dir)

def lemstrom():
    client.index_notes_write_response(os.path.join(LEMSTROM, "leiermann.xml"), LEMSTROM)
    for q in ("a", "b", "c", "d", "e", "f"):
        query = f"query_{q}.mid"
        midi_file_path = os.path.join(LEMSTROM, query)
        client.index_notes_write_response(midi_file_path, LEMSTROM)

def other():
    client.index_notes_write_response(os.path.join(TESTDATA, "000000000000457_Castigans-castigavit_Josquin-Des-Prez_file3.xml"), TESTDATA)
    client.index_notes_write_response(os.path.join(TESTDATA, "000000000000458_Castigans-castigavit_Josquin-Des-Prez_file4.midi"), TESTDATA)

def queries():
    CG_E = smr_pb2.IndexResponse(notes = (
        smr_pb2.Note(onset=0, offset=1, pitch_b40=162, piece_idx=0), # C G
        smr_pb2.Note(onset=0, offset=1, pitch_b40=185, piece_idx=1),
        smr_pb2.Note(onset=1, offset=2, pitch_b40=174, piece_idx=2)) # E
    )
    with open(os.path.join(QUERIES, "CG_E.idxresp_notes"), "wb") as f:
        f.write(CG_E.SerializeToString())

    double_leading_tone = smr_pb2.IndexResponse(notes = (
        smr_pb2.Note(onset=0, offset=1, pitch_b40=162, piece_idx=0), # C E A C
        smr_pb2.Note(onset=0, offset=1, pitch_b40=174, piece_idx=1),
        smr_pb2.Note(onset=0, offset=1, pitch_b40=191, piece_idx=2),
        smr_pb2.Note(onset=0, offset=1, pitch_b40=202, piece_idx=3),
        smr_pb2.Note(onset=1, offset=2, pitch_b40=156, piece_idx=4), # Bb D F Bb
        smr_pb2.Note(onset=1, offset=2, pitch_b40=168, piece_idx=5),
        smr_pb2.Note(onset=1, offset=2, pitch_b40=179, piece_idx=6),
        smr_pb2.Note(onset=1, offset=2, pitch_b40=196, piece_idx=7))
    )
    with open(os.path.join(QUERIES, "double_leading_tone.idxresp_notes"), "wb") as f:
        f.write(double_leading_tone.SerializeToString())

if __name__ == "__main__":
    queries()
    other()
    palestrina()
    lemstrom()
