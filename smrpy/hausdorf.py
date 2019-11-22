import sys
import os
from smrpy import indexers
import music21
import itertools
import psycopg2
from tqdm import tqdm
from io import StringIO
from collections import Counter
from dataclasses import dataclass

try:
    plpy
except NameError:
    plpy = False
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()

def log(msg):
    if plpy:
        plpy.warning(msg)
    else:
        logger.debug(msg)

WINDOW = 10
BINS = {}

def stream_to_xml(stream):
  sx = music21.musicxml.m21ToXml.ScoreExporter(stream)
  musicxml = sx.parse()
  bfr = StringIO()
  sys.stdout = bfr
  sx.dump(musicxml)
  output = bfr.getvalue()
  sys.stdout = sys.__stdout__
  return output

def execute(sql_query):
  conn = psycopg2.connect("")
  with conn, conn.cursor() as cur:
    return cur.execute(sql_query)

@dataclass
class Piece:
  data: bytes
  fmt: str = ""
  name: str = ""
  collection_id: int = 0

  def __post_init__(self):
    stream = music21.converter.parse(self.data)
    self.xml = stream_to_xml(stream)
    self.notes = [Note(n.offset, n.offset + n.duration.quarterLength, n.pitch.ps, i) for i, n in enumerate(indexers.NotePointSet(stream))]
    self.windows = list(generate_normalized_windows(stream, WINDOW))

  def insert_postgres(self):
    conn = psycopg2.connect("")
    with conn, conn.cursor() as cur:
      print("inserting piece")
      cur.execute(
        """
        INSERT INTO Piece (fmt, data, name, collection_id)
        VALUES (%s, %s, %s, %s)
        RETURNING pid;
        """, (self.fmt, bytes(self.xml, encoding='utf-8'), self.name, self.collection_id))
      pid, = cur.fetchone()
      print("inserting notes")
      cur.execute(
        """
        INSERT INTO Note(n, pid, nid)
        VALUES""" + ", ".join(["('( %s, %s )', %s, %s)" for n in self.notes]) + ";", [x for lst in [(n.onset, n.pitch, pid, n.index) for n in self.notes] for x in lst])

      print("inserting windows and postings")
      for (u, v), w in tqdm(self.windows):
        cur.execute(
          """
          INSERT INTO NormalizedWindow(pid, u, v, len)
          VALUES (%s, %s, %s, %s);""", (pid, u.index, v.index, len(w)))
          #, '{ """ + ", ".join(["(%s, %s)" for n in w]) + " }')" + ";", [pid, u.index, v.index, len(w)] + [x for lst in [(n.onset, n.pitch) for n in w] for x in lst])

        for i, n in enumerate(w[1:], 1):
            cur.execute(
                """
                INSERT INTO Posting(n, pid, u, v, nid)
                VALUES ('(%s, %s)', %s, %s, %s, %s);""", (n.onset, n.pitch, pid, u.index, v.index, n.index))



def query_postgres(stream):
    conn = psycopg2.connect("")
    matches = {}
    query_length = len(indexers.NotePointSet(stream))
    (u, v), window = next(generate_normalized_windows(stream, query_length))
    with conn, conn.cursor() as cur:
        for n in window:
            cur.execute(f"SELECT * FROM Posting WHERE n ~= '{(n.onset, n.pitch)}'");
            postings = cur.fetchall()
            for _, _, pid, u, v, j in postings:
                key = (pid, u, v)
                matches[key] = matches.get(key, (u,)) + ((j, n.index),)

    return set(v for v in matches.values() if len(v) >= query_length)
       
@dataclass
class Note:
    onset: int
    duration: int
    pitch: int
    index: int
    
    def __hash__(self):
      return hash((self.onset, self.pitch))

    def insert_str(self):
        return
        """
        INSERT INTO Note(n, pid, nid)
        VALUES ('( %s, %s )', %s, %s);
        """,
        ("integer",) * 4
        (n.onset, n.pitch, pid, n.index)

    def insert(self):
      query, types, values = self.insert_str()
      if plpy:
        plan = plpy.prepare(query, types)
        plan.execute(values)
      else:
        execute(query)

def normalize(window, basis):
    u, v = basis
    normalized_window = []
    for note in window:
        normed_pitch = note.pitch - u.pitch
        normed_onset = (note.onset - u.onset) / abs(v.onset - u.onset)
        normalized_window.append(Note(normed_onset, 0, normed_pitch, note.index))
    return normalized_window

def query(stream):
    m = []
    query_length = len(indexers.NotePointSet(stream))
    for (u, v), window in generate_normalized_windows(stream, query_length):
        print(window)
        matches = {}
        for n in window:
            postings = BINS.get(n.__hash__(), ())
            for (u, v), j in postings:
                key = (u, v)
                matches[key] = matches.get(key, (u,)) + ((j, n.index),)
        m.append(matches)
    return set((c[key]) for c in m for key in c if len(c[key]) >= query_length)


# note1: b1, b2, b3, ...
# note2: b1, b5, b6, ...

# b1: note1, note2

# note1: (w_i, n_j)
# note1: (w_i, n_j)

def index(stream, bins):
    for (u, v), normalized_window in generate_normalized_windows(stream, WINDOW):
        for i, normalized_note in enumerate(normalized_window[1:], 1):
            bins[normalized_note.__hash__()] = bins.get(normalized_note.__hash__(), ()) + (((u.index, v.index), normalized_window[i].index),)

def generate_normalized_windows(stream, window_size):
    notes = [Note(n.offset, n.offset + n.duration.quarterLength, n.pitch.ps, i) for i, n in enumerate(indexers.NotePointSet(stream))]
    
    for i in range(min(len(notes) - window_size + 1, len(notes))):
        window = notes[i:i+window_size]
        bases = [(window[0], window[i]) for i in range(1, len(window))]
        for u, v in ((u, v) for u, v in bases if u.onset != v.onset):
            yield (u,v), normalize(window, (u,v)), window

def generate_normalized_windows_with_notes(notes, window_size):
    
    for i in range(min(len(notes) - window_size + 1, len(notes))):
        window = notes[i:i+window_size]
        bases = [(window[0], window[i]) for i in range(1, len(window))]
        for u, v in ((u, v) for u, v in bases if u.onset != v.onset):
            yield (u,v), normalize(window, (u,v)), window

def parse_filename(path):
  fmt = path[-3:]
  name = os.path.basename(path)
  return fmt, name

if __name__ == "__main__":
  control = sys.argv[1]
  filename = sys.argv[2]
  if control == "index":
    with open(filename, "rb") as f:
        data = f.read()
    fmt, name = parse_filename(filename)
    p = Piece(data=data, fmt=fmt, name=name)
    p.insert_postgres()

    #s = music21.converter.parse("tests/testdata/lemstrom2011/leiermann.xml")
    #q = music21.converter.parse("tests/testdata/lemstrom2011/query_a.mid")
    #index(s)
    #m = query(q) 
    #print(m)
