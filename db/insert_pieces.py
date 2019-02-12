import psycopg2
import os
import music21
from indexers import indexers
from tqdm import tqdm

ELVIS_DUMP = os.environ['ELVISDUMP']

DBSTRING = 'host=localhost dbname=postgres user=postgres password=postgres'

CONN = psycopg2.connect(DBSTRING)
CONN.autocommit = True


def index_vectors():
  query_unindexed_pieces = f"""
    SELECT music.pieces.id, diskpath FROM music.pieces
    WHERE music.pieces.id IN (
    SELECT piece_id from index.notes)
    AND music.pieces.id NOT IN (
    SELECT piece_id from index.intra_vectors);
  """

  with CONN, CONN.cursor() as cur:
    cur.execute(query_unindexed_pieces)
    unindexed_pieces = cur.fetchall()

    for piece_id, diskpath in tqdm(unindexed_pieces):
      with open(diskpath, 'r') as f:

        try:
          score = music21.converter.parse(f.read())
          vectors = indexers.legacy_intra_vectors(score, 10)[['x', 'y', 'startIndex', 'endIndex']]
        except Exception:
          continue

        for _, x, y, start, end in vectors.itertuples():
          cur.execute(
            f"""
            INSERT INTO index.intra_vectors (piece_id, vector, left_id, right_id)
            VALUES ('{piece_id}', '({x}, {y})', '{start}', '{end}');
          """)

def index_notes():
  query_unindexed_pieces = f"""
    SELECT music.pieces.id, diskpath FROM music.pieces
    WHERE music.pieces.id NOT IN (
      SELECT piece_id from index.notes
    );
  """

  with CONN, CONN.cursor() as cur:
    cur.execute(query_unindexed_pieces)
    unindexed_pieces = cur.fetchall()

    for piece_id, diskpath in tqdm(unindexed_pieces):
      with open(diskpath, 'r') as f:
        print(f"processing {diskpath}")

        try:
          score = music21.converter.parse(f.read())
          notes = indexers.note_index(score)[['offset', 'pitch-b40']]
        except Exception:
          continue

        for _, o, p in notes.itertuples():
          cur.execute(
            f"""
            INSERT INTO index.notes (piece_id, note)
            VALUES ('{piece_id}', '({o}, {p})');
          """)

def insert_piece_to_db(fullpath):
  dumpname, format = os.path.splitext(os.path.basename(fullpath))
  _, _, name = dumpname.partition('_')

  query = f"""
    INSERT INTO music.pieces(name, format, diskpath)
    VALUES('{name}', '{format[1:]}', '{fullpath}');
  """

  with CONN, CONN.cursor() as cur:
    cur.execute(query)

def insert_elvis_subdir(subdir):
  subdir_path = os.path.join(os.path.abspath(ELVIS_DUMP), subdir)

  for fname in tqdm(os.listdir(subdir_path)):
    fullpath = os.path.join(subdir_path, fname)
    insert_piece_to_db(fullpath)

def main():
  pass
  #insert_elvis_subdir('MEI')
  #index_notes()

if __name__ == '__main__':
  main()