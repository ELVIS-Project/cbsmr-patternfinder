CREATE TABLE IF NOT EXISTS Piece (
  pid SERIAL PRIMARY KEY,
  fmt TEXT,
  symbolic_data TEXT,
  music21_xml TEXT,
  composer TEXT,
  name TEXT,
  filename TEXT,
  collection_id INTEGER
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
