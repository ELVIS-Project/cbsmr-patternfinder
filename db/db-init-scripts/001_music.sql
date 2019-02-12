CREATE SCHEMA IF NOT EXISTS music;

CREATE TABLE IF NOT EXISTS music.collections (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS music.pieces (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  format TEXT NOT NULL,
  diskpath TEXT NOT NULL,
  collection_name varchar(80) references music.collections(name)
);
