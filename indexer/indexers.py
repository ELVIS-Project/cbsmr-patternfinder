import sys
import os
import csv
import io
import xml.etree.ElementTree as ET
import base64
import music21
import pandas as pd
import numpy as np
from indexer.errors import *

us = music21.environment.UserSettings()
us.restoreDefaults()

def _note_indexer(note):
    return {
        'onset': note.offset,
        'offset': note.offset + note.duration.quarterLength,
        'pitch-chr': note.pitch.ps,
        'pitch-dia': note.pitch.diatonicNoteNum,
        'pitch-b40': music21.musedata.base40.pitchToBase40(note),
    }

def notes_to_sql(df_notes, piece_id):
    sub_df = df_notes[['onset', 'offset', 'pitch-b40']]
    return f"""
        INSERT INTO Note (piece_id, piece_idx, onset, "offset", "pitch-b40")
        VALUES {", ".join([f"('{piece_id}', {idx}, '{float(on)}', '{float(off)}', '{p}')" for idx, (_, on, off, p) in enumerate(sub_df.itertuples())])}
        """

def notes(symbolic_data):
    try:
        m21_score = music21.converter.parse(symbolic_data)
    except Exception as e:
        raise music21.Music21Exception from e

    # Returning an empty index is not desirable behaviour. User should be aware
    # that no notes were extracted from the score they provided.
    if len(m21_score.flat.notes) == 0:
        raise EmptyScoreError

    notes = list(NotePointSet(m21_score))
    indexed_notes = (_note_indexer(n) for n in notes)

    return pd.DataFrame(indexed_notes).sort_values(by=["onset", "pitch-b40"])

def intra_vectors_to_sql(df_intra_vectors, piece_id):
    sub_df = df_intra_vectors[['onset', 'pitch-b40', 'startIndex', 'endIndex']]
    return f"""
        INSERT INTO intra_vectors (piece_id, vector, left_id, right_id)
        VALUES {", ".join([f"('{piece_id}', '({float(x)}, {float(y)})', {start}, {end})" for _, x, y, start, end in sub_df.itertuples()])}
        """

def intra_vectors(symbolic_data):
    df = notes(symbolic_data)

    intervals = []
    for window in range(1, 2):
        vectors = df.diff(periods = window).dropna()

        vectors['window'] = window
        vectors['startIndex'] = vectors.index - window
        vectors['endIndex'] = vectors.index

        intervals.append(vectors)

    return pd.concat(intervals, axis=0) \
            .sort_values(by=["pitch-b40", "startIndex"]) \
            .reset_index(drop=True)

def legacy_intra_vectors_to_sql(df_intra_vectors, piece_id):
    sub_df = df_intra_vectors[['x', 'y', 'startIndex', 'endIndex', 'startPitch', 'endPitch', 'diatonicDiff', 'chromaticDiff']]
    return f"""
        INSERT INTO legacy_intra_vectors (piece_id, x, y, startIndex, endIndex, startPitch, endPitch, diatonicDiff, chromaticDiff)
        VALUES {", ".join([f"('{piece_id}', '{float(x)}', '{float(y)}', '{start}', '{end}', '{float(startPitch)}', '{float(endPitch)}', '{float(chromaticDiff)}', '{float(diatonicDiff)}')"
        for _, x, y, start, end, startPitch, endPitch, chromaticDiff, diatonicDiff in sub_df.itertuples()])}
        """

def legacy_intra_vectors(piece, window):

    df = notes(piece)

    intervals = []
    for window in range(1, window + 1):
        vectors = df.diff(periods = window).dropna()
        vectors['window'] = window

        vectors['x'] = vectors['offset']
        vectors['y'] = vectors['pitch-chr'].astype('int32')
        vectors['startIndex'] = vectors.index - window
        vectors['endIndex'] = vectors.index
        vectors['startPitch'] = df['pitch-chr'].shift(window)
        vectors['endPitch'] = df['pitch-chr']
        vectors['chromaticDiff'] = vectors['pitch-chr'].astype('int32')
        vectors['diatonicDiff'] = vectors['pitch-dia'].astype('int32')

        intervals.append(vectors)

    df = pd.concat(intervals, axis=0).sort_values(by=["y", "startIndex"])

    return df

def legacy_intra_vectors_to_csv(df):

    file_obj = io.StringIO()

    csv_writer = csv.writer(file_obj, delimiter=',')
    csv_writer.writerow(['x', 'y', 'startIndex', 'endIndex', 'startPitch', 'endPitch', 'diatonicDiff', 'chromaticDiff'])
    csv_writer.writerow([len(set(df.index))])
    csv_writer.writerow([len(df.index)])

    df.to_csv(
        columns=['x', 'y', 'startIndex', 'endIndex', 'startPitch', 'endPitch', 'diatonicDiff', 'chromaticDiff'],
        path_or_buf = file_obj,
        index=False,
        header=False)

    output = file_obj.getvalue()
    file_obj.close()
    return output

def parse_piece_path(piece_path):
    basename, fmt = os.path.splitext(os.path.basename(piece_path))
    fmt = fmt[1:] # skip '.'
    base = [x for x in os.path.basename(basename).split("_") if not "file" in x]

    piece_id = base[0]
    name = base[1]
	#name = base[1].replace('-', ' ')
	#composer = base[2].replace('-', ' ')
    composer = ""
    corpus = 'elvis'

    return piece_id, name, composer, corpus, fmt

def music21Chord_to_music21Notes(chord):
    """
    For internal use in NotePointSet()

    CHORD TO LIST OF NOTES FOR USE IN music21.stream.insert()
    For serious flattening of the score into a 2-d plane of horizontal line segments.
    music21.note.Note and music21.chord.Chord subclass the same bases,
    so in theory it shoud look something like this...

    NOTE: this will screw up the coloring since music21 doesn't support coloring just
    one note of a chord (I don't think?), so as a compromise I'll just color the whole chord.
    """
    note_list = []
    for pitch in chord.pitches:
        note = music21.note.Note(pitch)

        # Music21Object.mergeAttributes gets the 'id' and 'group' attributes
        note.mergeAttributes(chord)

        # note essentials
        note.duration = chord.duration
        note.offset = chord.offset

        note_list.append(note)

        note.derivation.origin = chord
        note.derivation.method = 'chord_to_notes'
    return note_list

class NotePointSet(music21.stream.Stream):
    """
    A container for the notes of a music21 parsed score.
    Pre-processes the data by flattening the chords and sorting the notes.

    Expects a stream to process
    Optionally can be flagged to sort by offset (note release) rather than the default onset (note attack)

    music21.stream.Stream does not allow any required arguments in its __init__, so every argument must be optional.
    """
    def __init__(self, score=music21.stream.Stream(), offsetSort=False, *args, **kwargs):
        super(NotePointSet, self).__init__()
        # Set the derivation for this PointSet
        self.derivation.method = 'NotePointSet()'
        self.derivation.origin = score

        # If we have None input, return an empty stream
        if not score:
            return

        # Sorting key for the NotePointSet: sort lexicographicaly by tuples of:
        #    1) either note onset (attack) or note offset (release)
        #    2) note frequency
        #        -- Since this is the most finely-grained pitch information possible,
        #        the list will still be sorted under any subsequent pitch equivalence
        #        (such as pitch class or enharmonic equivalence)
        sort_keyfunc = lambda n: ((n.offset + n.duration.quarterLength, n.pitch.frequency)
                if offsetSort else (n.offset, n.pitch.frequency))

        # Get each note or chord, convert it to a tuple of notes, and sort them by the keyfunc
        new_notes = []
        for note in score.flat.notes:
            to_add = music21Chord_to_music21Notes(note)
            # Use .original_note instead of derivation chains. It has to be consistent:
            # you can't be checking different derivations for notes which came from chords
            # versus notes which were not derived. If for example a source was transposed
            # (like in the test cases), the derivation will be non-empty, which screws up
            # the decision making for occurrences later on.
            for n in to_add:
                n.original_note_id = note.id
            new_notes.extend(to_add)
        new_notes.sort(key=sort_keyfunc)

        # Make sure to turn off stream.autoSort, since streams automatically sort on insert by
        # an internal sortTuple which prioritizes note onset (attack)
        self.autoSort = False
        for n in new_notes:
            self.insert(n)


def index_measures(symbolic_data):
    measures = []

    m21_score = music21.converter.parse(symbolic_data)

    nps = NotePointSet(music21.converter.parse(symbolic_data))
    m21_measures = list(m21_score.measures(1, None).recurse(classFilter=['Measure']))
    for m21_measure in m21_measures:
        note_idx = 0

        measure_out = m21_measure.write('xml')
        with open(measure_out, 'rb') as f:
            data = base64.b64encode(f.read())
        os.remove(measure_out)

        while nps[note_idx].offset < m21_measure.offset and note_idx < len(nps) - 1:
            note_idx += 1

        measures.append((data, m21_measure.number, note_idx))

    return measures


def index_and_insert_measures(symbolic_data, piece_id, db_conn):
    m21_score = music21.converter.parse(symbolic_data)

    #print("Hanging on MakeMeasures", flush=True)
    #measured_score = m21_score.makeMeasures()
    #print("enumerating measures", flush=True)
    #enumerated_measures = enumerate(measured_score)

    nps = NotePointSet(music21.converter.parse(symbolic_data))
    m21_measures = list(m21_score.measures(1, None).recurse(classFilter=['Measure']))
    for m21_measure in m21_measures:
        notes_idx = 0
        print(m21_measure.number, end=' ', flush=True)
        measure_out = m21_measure.write('xml')
        with open(measure_out, 'rb') as f:
            data = base64.b64encode(f.read()).decode('utf-8')

        while nps[notes_idx].offset < m21_measure.offset:
            notes_idx += 1

        with db_conn, db_conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO Measure (pid, mid, nid, onset, data)
                VALUES ('{piece_id}', '{m21_measure.number}', '{notes_idx}', '{float(m21_measure.offset)}', '{data}')
            """)

if __name__ == "__main__":

    if (len(sys.argv) < 3):
        print("indexers.py method input")
        sys.exit(0)

    method = sys.argv[1]
    input = sys.argv[2]
    input_fullpath = os.path.abspath(input)
    input_filename, ext = os.path.splitext(input_fullpath)

    import indexers
    func = getattr(indexers, method)

    with open(input_fullpath, 'r') as f:
        symbolic_data = f.read()

    df = func(symbolic_data)
    
    with open(input_filename + '.' + method, 'w') as f:
        df.to_csv(f)

"""
    if (len(sys.argv) < 1) or (sys.argv[1] in ("-h", "--help")):
        print("indexers.py input_dir output_dir")

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    failed = []

    for piece in os.listdir(input_dir):
        full_path = os.path.join(input_dir, piece)
        piece_name = os.path.splitext(piece)[0]

        print("Indexing " + full_path)

        try:
            score = music21.converter.parse(full_path)
            csv_file = legacy_intra_vectors(score, 10)
        except Exception:
            failed.append(piece)

        with open(os.path.join(output_dir, piece_name + '.vectors'), 'w') as f:
            f.write(csv_file)

    if len(failed) > 0:
        print("Failed some pieces...\n{}".format("\n".join(failed)))
"""