import sys
import os
import io
import csv
import music21
import pandas as pd
import numpy as np
from smrpy.piece import Note
from itertools import groupby

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

def parse(symbolic_data):
    try:
        m21_score = music21.converter.parse(symbolic_data)
    except Exception as e:
        raise music21.Music21Exception from e
    
    # Returning an empty index is not desirable behaviour. User should be aware
    # that no notes were extracted from the score they provided.
    if len(m21_score.flat.notes) == 0:
        raise EmptyScoreError

    return m21_score

def notes(m21_score):

    notes = list(NotePointSet(m21_score))
    indexed_notes = (_note_indexer(n) for n in notes)

    return pd.DataFrame(indexed_notes).sort_values(by=["onset", "pitch-chr"])

def pb_notes(m21_score):
    ns = notes(m21_score)[['onset', 'offset', 'pitch-chr']]
    pb_notes = [smr_pb2.Note(
        onset=on,
        offset=off,
        pitch=int(p),
        piece_idx=idx)
        for idx, (_, on, off, p) in enumerate(ns.itertuples())]
    pb_notes.sort(key=lambda n: (n.piece_idx))
    return pb_notes

def intra_vectors(piece, window):

    sc = parse(piece)
    df = notes(sc)

    intervals = []
    for window in range(1, min(window + 1, len(df))):
        vectors = df.diff(periods = window).dropna()
        vectors['window'] = window

        vectors['x'] = vectors['onset']
        vectors['y'] = vectors['pitch-chr'].astype('int32')
        vectors['startIndex'] = vectors.index - window
        vectors['endIndex'] = vectors.index
        intervals.append(vectors)

    df = pd.concat(intervals, axis=0).sort_values(by=["y", "startIndex"])
    return df

def intra_vectors_to_csv(df):

    file_obj = io.StringIO()
    csv_writer = csv.writer(file_obj, delimiter=',')
    csv_writer.writerow(['x', 'y', 'startIndex', 'endIndex'])
    # the df.diff() takes vectors between notes, so the indices must be incremented
    csv_writer.writerow([len(set(df.index)) + 1])
    csv_writer.writerow([len(df.index)])

    df.to_csv(
        columns=['x', 'y', 'startIndex', 'endIndex'],
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

        # Pointer to original stream
        self.original_stream = score

        # Make sure to turn off stream.autoSort, since streams automatically sort on insert by
        # an internal sortTuple which prioritizes note onset (attack)
        self.autoSort = False
        for n in new_notes:
            self.insert(n)

def m21_score_to_xml_write(m21_score):
    o = m21_score.write('xml')
    with open(o, 'rb') as f:
        xml = f.read()
    os.remove(o)
    return xml

def m21_xml(stream):
    nps = list(NotePointSet(stream))
    nps_ids = [n.id for n in nps]
    sort_by_onid = lambda n: n.original_note_id
    nps_sorted_by_onid = sorted(nps, key=sort_by_onid)
    for og_nid, nps_notes in groupby(nps_sorted_by_onid, key=sort_by_onid):
        for nps_note in nps_notes:
            note = Note.from_m21(nps_note, nps_ids.index(nps_note.id))
            note_comment = music21.editorial.Comment(f"<nid>{note.index}</nid>")
            og_note = list(stream.flat.notes)[[n.id for n in list(stream.flat.notes)].index(og_nid)]
            og_note.editorial.footnotes.append(note_comment)
    return m21_score_to_xml_write(stream)
        

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
