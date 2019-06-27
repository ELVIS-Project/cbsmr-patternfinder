import sys
import os
import csv
import music21
from indexer import client, indexers
from proto import smr_pb2, smr_pb2_grpc

CURDIR = os.path.abspath(os.path.dirname(__file__))
PROJROOT = os.path.join(CURDIR, os.pardir)
HELSINKI_TESTS = os.path.join(PROJROOT, "smr", "helsinki-ttwi", "tests")
TESTDATA = os.path.join(CURDIR, "testdata")
PALESTRINA = os.path.join(TESTDATA, "palestrina_masses")
LEMSTROM = os.path.join(TESTDATA, "lemstrom2011")
QUERIES = os.path.join(TESTDATA, "queries")

def helsinki_ttwi():

    for filename in ("leiermann.xml", "query_a.mid", "query_b.mid", "query_c.mid", "query_d.mid", "query_e.mid", "query_f.mid"):
        filename_without_extension = os.path.splitext(os.path.basename(filename))[0]
        with open(os.path.join(LEMSTROM, filename), "rb") as f:
            data = f.read()
            notes_df = indexers.notes(data)
            vectors_df = indexers.intra_vectors(data, len(notes_df))
            vectors_csv = indexers.intra_vectors_to_csv(vectors_df)

        with open(os.path.join(HELSINKI_TESTS, filename_without_extension + ".csv"), "w", newline="") as csvfile:
            csvfile.write(vectors_csv)

    palestrina_occs = (
        #("000000000011344_Missa-Primi-toni_Credo_Palestrina-Giovanni-Pierluigi-da_file2.mid", 1238, 1266),)
        ("/Users/davidgarfinkle/elvis-project/patternfinder/music_files/corpus/Palestrina/Primi_toni_Credo_4.mid", 1238, 1266),)

    for mass, start, end in palestrina_occs:
        filename_without_extension = os.path.splitext(os.path.basename(mass))[0]
        #with open(os.path.join(PALESTRINA, "mid", mass), "rb") as f:
        with open(mass, "rb") as f:
            data = f.read()
            vectors_df = indexers.intra_vectors(data, len(notes_df))
            vectors_df = vectors_df[(vectors_df['startIndex'] >= 1238) & (vectors_df['endIndex'] <= 1266)]
            vectors_csv = indexers.intra_vectors_to_csv(vectors_df)

        print(vectors_csv)
        with open(os.path.join(HELSINKI_TESTS, filename_without_extension + ".csv"), "w", newline="") as csvfile:
            csvfile.write(vectors_csv)

    query = music21.stream.Score()
    query.insert(0, music21.chord.Chord(['C4', 'E4', 'A4', 'C5']))
    query.insert(1, music21.chord.Chord(['B-3', 'F4', 'B-4', 'D5']))
    outpath = query.write('xml')
    with open(outpath, "r") as f:
        data = f.read()
        double_leading_tone_query_notes = indexers.notes(data)
        double_leading_tone_query_vectors = indexers.intra_vectors(data, len(double_leading_tone_query_notes))
    with open(os.path.join(HELSINKI_TESTS, "double_leading_tone_query.csv"), "w", newline="") as csvfile:
        csvfile.write(indexers.intra_vectors_to_csv(double_leading_tone_query_vectors))


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
    helsinki_ttwi()
    lemstrom()
    queries()
    other()
    palestrina()
