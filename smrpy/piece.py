import sys
import os
import music21
import base64
import psycopg2.extensions
import ast
from itertools import combinations
from smrpy import piece, indexers, metadata
from proto import smr_pb2
from dataclasses import dataclass

def m21_score_to_xml_write(m21_score):
    o = m21_score.write('xml')
    with open(o, 'rb') as f:
        xml = f.read()
    os.remove(o)
    return xml

@dataclass
class Piece:
  data: str
  md: metadata.Metadata
  music21_xml: bytes = b''
  notes: tuple = ()

  def __post_init__(self):
    stream = music21.converter.parse(self.data)
    stream.makeNotation(inPlace=True)
    self.music21_xml = indexers.m21_xml(stream)
    self.notes = [piece.Note(n.offset, n.offset + n.duration.quarterLength, n.pitch.ps, i) for i, n in enumerate(indexers.NotePointSet(stream))]
  
  def insert_str(self):
    if self.md.pid: 
        vt = (
            (self.md.pid, "integer"),
            (self.md.fmt, "text"),
            (self.data, "text"),
            (base64.b64encode(self.music21_xml).decode('utf-8'), "text"),
            (self.md.name, "text"),
            (self.md.collection_id, "integer"))
        values, types = zip(*vt)
        return ("""
        INSERT INTO Piece (pid, fmt, symbolic_data, music21_xml, name, collection_id)
        VALUES(%s, %s, %s, %s, %s, %s)
        ON CONFLICT ON CONSTRAINT piece_pkey DO
        UPDATE SET (symbolic_data, name, composer, fmt, filename, collection_id) = (%s, %s, %s, %s, %s, %s)
        RETURNING pid;
        """, types, values)
    else:
        return ("""
        INSERT INTO Piece (fmt, data, name, collection_id)
        VALUES(%s, %s, %s, %s)
        RETURNING pid;
        """, types[1:], values[1:])

@dataclass
class Note:
    onset: float
    duration: int
    pitch: int
    index: int

    def __post_init__(self):
        self.onset = float(self.onset)
        self.pitch = int(self.pitch)
    
    def __hash__(self):
      return hash((self.onset, self.pitch))

    @classmethod
    def from_m21(cls, p, idx):
        return cls(onset=p.offset, pitch=p.pitch.ps, duration=p.duration.quarterLength, index=idx)

    def __str__(self):
        return str((float(self.onset), self.pitch))

    def __repr__(self):
        return str((self.index, self.onset, self.pitch, self.duration))

    def insert_str(self, pid):
        return ("""
        INSERT INTO Note(n, pid, nid)
        VALUES (%s, %s, %s);
        """,
        ("point", "integer", "integer"),
        (self, pid, self.index))

    def getquoted(self):
        o = psycopg2.extensions.adapt(self.onset).getquoted()
        p = psycopg2.extensions.adapt(self.pitch).getquoted()
        return b"'(%s, %s)'" % (o, p)

    def __conform__(self, proto):
        if proto is psycopg2.extensions.ISQLQuote:
            return self

    def to_pb(self, piece_idx = None):
        return smr_pb2.Note(onset=self.onset, offset=(self.onset + self.duration), pitch=int(self.pitch), piece_idx = piece_idx if piece_idx else self.index)

    @classmethod
    def from_pb(cls, pb_note):
        return cls(onset=pb_note.onset, pitch=pb_note.pitch, duration=(pb_note.offset - pb_note.onset), index=pb_note.piece_idx)

    def to_point(self):
        return (float(self.onset), self.pitch)

    def eq_2d(self, other):
        return self.onset == other.onset and self.pitch == other.pitch

    @classmethod
    def from_point(cls, idx, inp):
        p = ast.literal_eval(inp)
        return cls(p[0], None, p[1], idx)

    @classmethod
    def from_repr(cls, repr_str):
        p = ast.literal_eval(repr_str)
        return cls(*p)

def filter_bases(bases):
    for i, (u, v) in enumerate(bases):
        preds = []
        preds.append(u.onset != v.onset)
        if i > 1:
            prev_u, prev_v = bases[i - 1]
            preds.append(v.onset != prev_v.onset)
        if all(preds):
            yield (u, v)

@dataclass
class NoteWindow:
    pid: int
    u: int
    v: int
    notes: tuple
    normalized_notes: tuple = ()

    def __post_init__(self):
        self.normalized_notes = self.normalize()

    @classmethod
    def from_notes(cls, pid, notes, window_size):
        assert window_size > 1
        # :todo handle case window_size > len(notes)
        num_windows = len(notes) - window_size + 1
        windows = []
        for i in range(num_windows):
            bases = []
            window = notes[i : i + window_size]
            if i == num_windows - 1:
                for u, v in combinations(window, 2):
                    bases.append((u, v))
            else:
                for n in window[1:]:
                    bases.append((window[0], n))

            for u, v in filter_bases(bases):
                yield cls(pid, u, v, window)
            
    def normalize(self):
        normalized_window = []
        u, v = self.u, self.v
        for note in self.notes:
            normed_pitch = note.pitch - u.pitch
            normed_onset = (note.onset - u.onset) / abs(v.onset - u.onset)
            normalized_window.append(Note(normed_onset, 0, normed_pitch, note.index))
        return normalized_window

    def to_string(self):
        return "{" + ','.join(f'\"({x.onset},{x.pitch})\"' for x in self.normalized_notes) + "}"

