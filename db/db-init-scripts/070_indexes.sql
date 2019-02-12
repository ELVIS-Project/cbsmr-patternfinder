CREATE SCHEMA IF NOT EXISTS index;
GRANT USAGE ON SCHEMA index TO indexer;

ALTER DEFAULT PRIVILEGES IN SCHEMA index
GRANT INSERT, SELECT ON TABLES TO indexer;

CREATE TABLE IF NOT EXISTS index.notes (
  id SERIAL PRIMARY KEY,
  piece_id INT NOT NULL references music.pieces(id),
  note POINT NOT NULL
);

CREATE TABLE IF NOT EXISTS index.intra_vectors (
  id SERIAL PRIMARY KEY,
  piece_id INT NOT NULL references music.pieces(id),
  vector POINT NOT NULL,
  left_id INT NOT NULL references index.notes(id),
  right_id INT NOT NULL references index.notes(id),
  UNIQUE (piece_id)
)
