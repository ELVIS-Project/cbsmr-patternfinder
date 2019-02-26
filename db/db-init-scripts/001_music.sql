CREATE SCHEMA IF NOT EXISTS music;

CREATE TABLE IF NOT EXISTS music.collections (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS music.pieces (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  vectors TEXT NOT NULL,
  num_notes INT NOT NULL,
  format TEXT,
  diskpath TEXT,
  collection_name varchar(80) references music.collections(name)
);

CREATE TABLE IF NOT EXISTS music.measures (
  id SERIAL PRIMARY KEY,
  pid INT NOT NULL,
  mid INT NOT NULL,
  data TEXT
);
