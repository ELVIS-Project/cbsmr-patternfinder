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
	onset REAL,
	data TEXT
);

CREATE TABLE Note (
	measure INT REFERENCES Measure(id),
	pid INT REFERENCES Piece(id),
	pidx INT,
	onset REAL,
	"offset" REAL,
	pitchb40 REAL,
	PRIMARY KEY (pid, pidx)
);

ALTER TABLE Measure ADD COLUMN nid INT;

CREATE TABLE Trigram (
	id SERIAL PRIMARY KEY,
	notes Note[3],
	document_frequency INT
);
