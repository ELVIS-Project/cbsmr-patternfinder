import sys
import base64
from io import StringIO

import music21
from indexer import indexers

def coloured_excerpt(db_conn, note_list, piece_id):
    note_list = [int(i) for i in note_list]

    with db_conn, db_conn.cursor() as cur:
        cur.execute(f"""
            SELECT data
            FROM Piece
            WHERE pid={piece_id}
            ;
            """)
        results = cur.fetchall()
        if not results:
            raise Exception(f"excerpts: no data found for piece {piece_id}!")

    score = music21.converter.parse(base64.b64decode(results[0][0]))
    score.makeNotation(inPlace=True)

    nps = list(indexers.NotePointSet(score))
    nps_ids = [nps[i].original_note_id for i in note_list]

    # Get stream excerpt
    _, start_measure = score.beatAndMeasureFromOffset(nps[note_list[0]].offset)
    _, end_measure = score.beatAndMeasureFromOffset(nps[note_list[-1]].offset + nps[note_list[-1]].duration.quarterLength - 1)
    excerpt = score.measures(numberStart=start_measure.number, numberEnd=end_measure.number)

    # Colour notes
    for note in excerpt.flat.notes:
        if note.id in nps_ids:
            note.style.color = 'red'

    # Delete part names (midi files have bad data)
    for part in excerpt:
        part.partName = ''

    sx = music21.musicxml.m21ToXml.ScoreExporter(excerpt)
    musicxml = sx.parse()

    bfr = StringIO()
    sys.stdout = bfr
    sx.dump(musicxml)
    output = bfr.getvalue()
    sys.stdout = sys.__stdout__

    return output

