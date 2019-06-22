import sys
import os
import csv
from indexer import client, indexers
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
        query = f"query_{q}"
        midi_file_path = os.path.join(LEMSTROM, query + ".mid")
        response = client.index_notes_write_response(midi_file_path, LEMSTROM)

def lemstrom_csv():
    # Vectors CSV for c library testing

    for path, filenames in (
        (LEMSTROM, ("leiermann.xml", "query_a.mid", "query_b.mid", "query_c.mid", "query_d.mid", "query_e.mid", "query_f.mid")),
        (os.path.join(PALESTRINA, "mid"), ("000000000011521_Missa-Ut-re-mi-fa-sol-la_Credo_Palestrina-Giovanni-Pierluigi-da_file2.mid",))):

        for filename in filenames:
            print(filename)
            filename_without_extension = os.path.splitext(os.path.basename(filename))[0]
            with open(os.path.join(path, filename), "rb") as f:
                data = f.read()
                notes_df = indexers.notes(data)
                vectors_df = indexers.intra_vectors(data, len(notes_df))
                vectors_csv = indexers.intra_vectors_to_csv(vectors_df)

            with open(os.path.join(path, filename_without_extension + ".csv"), "w", newline="") as csvfile:
                csvfile.write(vectors_csv)

"""
    for filename in ("leiermann.xml", "query_a.mid", "query_b.mid", "query_c.mid", "query_d.mid", "query_e.mid", "query_f.mid"):
        filename_without_extension = os.path.splitext(os.path.basename(filename))[0]
        with open(os.path.join(LEMSTROM, filename), "rb") as f:
            data = f.read()
            notes_df = indexers.notes(data)
            vectors_df = indexers.intra_vectors(data, len(notes_df))
            vectors_csv = indexers.intra_vectors_to_csv(vectors_df)

        with open(os.path.join(LEMSTROM, filename_without_extension + ".csv"), "w", newline="") as csvfile:
            csvfile.write(vectors_csv)
"""

def other():
    client.index_notes_write_response(os.path.join(TESTDATA, "000000000000457_Castigans-castigavit_Josquin-Des-Prez_file3.xml"), TESTDATA)
    client.index_notes_write_response(os.path.join(TESTDATA, "000000000000458_Castigans-castigavit_Josquin-Des-Prez_file4.midi"), TESTDATA)

def queries():
    CG_E = smr_pb2.IndexResponse(notes = (
        smr_pb2.Note(onset=0, offset=1, pitch=162, piece_idx=0), # C G
        smr_pb2.Note(onset=0, offset=1, pitch=185, piece_idx=1),
        smr_pb2.Note(onset=1, offset=2, pitch=174, piece_idx=2)) # E
    )
    with open(os.path.join(QUERIES, "CG_E.idxresp_notes"), "wb") as f:
        f.write(CG_E.SerializeToString())

    double_leading_tone = smr_pb2.IndexResponse(notes = (
        smr_pb2.Note(onset=0, offset=1, pitch=162, piece_idx=0), # C E A C
        smr_pb2.Note(onset=0, offset=1, pitch=174, piece_idx=1),
        smr_pb2.Note(onset=0, offset=1, pitch=191, piece_idx=2),
        smr_pb2.Note(onset=0, offset=1, pitch=202, piece_idx=3),
        smr_pb2.Note(onset=1, offset=2, pitch=156, piece_idx=4), # Bb D F Bb
        smr_pb2.Note(onset=1, offset=2, pitch=168, piece_idx=5),
        smr_pb2.Note(onset=1, offset=2, pitch=179, piece_idx=6),
        smr_pb2.Note(onset=1, offset=2, pitch=196, piece_idx=7))
    )
    with open(os.path.join(QUERIES, "double_leading_tone.idxresp_notes"), "wb") as f:
        f.write(double_leading_tone.SerializeToString())

if __name__ == "__main__":
    lemstrom_csv()
    lemstrom()
    queries()
    other()
    palestrina()
