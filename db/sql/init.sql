CREATE TABLE IF NOT EXISTS Piece (
  pid SERIAL PRIMARY KEY,
  fmt TEXT,
  symbolic_data TEXT,
  music21_xml TEXT,
  composer TEXT,
  name TEXT,
  filename TEXT,
  collection_id INTEGER,
  window_size INTEGER
);

CREATE TABLE IF NOT EXISTS MeasureOnsetMap (
  onset NUMERIC,
  mid INTEGER,
  pid INTEGER REFERENCES PIECE(pid),
  PRIMARY KEY (pid, mid, onset)
);

CREATE INDEX idx_mom_pid_onset ON MeasureOnsetMap(pid, onset);

CREATE TABLE IF NOT EXISTS Note (
  n POINT,
  pid INTEGER REFERENCES Piece(pid),
  nid INTEGER,
  PRIMARY KEY (pid, nid)
);

CREATE INDEX idx_note_nid ON Note(nid);

CREATE TABLE IF NOT EXISTS NoteWindow (
  pid INTEGER REFERENCES Piece(pid),
  onset_start NUMERIC,
  onset_end NUMERIC,
  u INTEGER, -- todo make this a single "scale" factor
  v INTEGER,
  note_ids INTEGER[],
  unnormalized POINT[],
  normalized POINT[],
  PRIMARY KEY (pid, u, v, onset_start, onset_end)
);

CREATE TABLE IF NOT EXISTS NoteVector (
    id SERIAL PRIMARY KEY,
    pid INTEGER REFERENCES Piece(pid),
    x NUMERIC,
    y INTEGER,
    l POINT,
    r POINT
);

CREATE TABLE IF NOT EXISTS EnumeratedNoteVector (
    pid INTEGER,
    x NUMERIC,
    y INTEGER,
    l POINT,
    r POINT,
    l_nid INTEGER,
    r_nid INTEGER,
    FOREIGN KEY (pid, l_nid) REFERENCES Note(pid, nid),
    FOREIGN KEY (pid, r_nid) REFERENCES Note(pid, nid),
    PRIMARY KEY (pid, l_nid, r_nid)
);
