CREATE TABLE Corpus (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  UNIQUE (name)
);

CREATE TABLE Composer (
	name VARCHAR(80) PRIMARY KEY
);

CREATE TABLE Piece (
	id SERIAL PRIMARY KEY,
	encoding CHAR(3),
  vectors TEXT,
	composer VARCHAR(80) REFERENCES Composer(name),
	corpus VARCHAR(80) REFERENCES Corpus(name),
	name VARCHAR(80),
	data TEXT
);

CREATE TABLE Measure (
	id SERIAL PRIMARY KEY,
	mid INT,
	pid INT REFERENCES Piece(id),
	nid INT REFERENCES Note(id),
	onset REAL,
	data TEXT
);

CREATE TABLE Note (
	id SERIAL PRIMARY KEY,
	measure INT REFERENCES Measure(id),
	piece_id INT REFERENCES Piece(id),
	piece_idx INT,
	onset REAL,
	"offset" REAL,
	"pitch-b40" REAL
);

CREATE TABLE Trigram (
	id SERIAL PRIMARY KEY,
	notes Note[3],
	document_frequency INT
);