import ast
import base64
import music21
import urllib.parse
import xml.etree.ElementTree as ET
import io
from itertools import combinations
from collections import namedtuple
from smrpy.indexers import NotePointSet, m21_xml
from smrpy.piece import Piece, Note, NoteWindow, m21_score_to_xml_write
from smrpy.excerpt import coloured_excerpt
from smrpy.occurrence import OccurrenceFilters, filter_occurrences

try:
    import plpy
except ImportError:
    plpy = False
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()

def log(msg):
    if plpy:
        plpy.warning(msg)
    else:
        logger.debug(msg)

def plpy_execute(query, types, values):
    assert query.count('%s') == len(types)
    assert len(types) == len(values)
    
    for i in range(len(values)):
        query = query.replace('%s', '$' + str(i + 1), 1)

    plan = plpy.prepare(query, types)
    return plpy.execute(plan, values)

def notes_from_input(inp):
    import json
    point_array = json.loads(inp)
    return [Note(p['x'], None, p['y'], i) for i, p in enumerate(point_array)]

def notes_from_points(inp):
    tuple_list = map(lambda string_tuple: ast.literal_eval(string_tuple), inp)
    return [Note(p[0], None, p[1], i) for i, p in enumerate(tuple_list)]

def symbolic_data_to_m21_xml(sd_b64):
    sd = base64.b64decode(sd_b64)
    stream = music21.converter.parse(sd)
    xml = m21_xml(stream)
    return xml.decode('utf-8')

def excerpt(m21_xml, nids, measure_start, measure_end, color='#FF0000'):
    stream = music21.converter.parse(m21_xml)
    excerpt = stream.measures(numberStart=measure_start, numberEnd=measure_end)
    m21_xml_excerpt = m21_score_to_xml_write(excerpt)
    root = ET.fromstring(m21_xml_excerpt)
    tree = ET.ElementTree(root)
    for note_tag in root.findall('.//footnote/..'):
        footnote_tag = note_tag.find('footnote')
        _, _, nid_str = footnote_tag.text.partition('=')
        nid_int = int(nid_str)
        if nid_int in nids:
            note_tag.attrib.update({'color': color})
            notehead_tag = ET.SubElement(note_tag, 'notehead', attrib={'color': color, 'parantheses': 'no'})
            notehead_tag.text = 'normal'
    output = io.StringIO()
    tree.write(output, encoding="unicode")
    return output.getvalue()

def generate_notes(music21_xml):
    st = music21.converter.parse(music21_xml)
    nps = indexers.NotePointSet(st)
    for i, n in enumerate(nps):
        yield {
            'pid': -1,
            'n': Note.from_m21(n, i).to_point(),
            'nid': i
        }

def measure_onset_map(music21_xml):
    st = music21.converter.parse(music21_xml)
    mm = st.flattenParts().measureOffsetMap()
    for onset, mms in mm.items():
        measure, = mms
        yield {
            'pid': -1,
            'mid': measure.number,
            'onset': onset
        }

def search_filtered(query, transpositions, intervening, inexact):
    occfilters = OccurrenceFilters(transpositions, intervening, inexact)
    results = search(query)
    for pid, nids, points in results:
        # :todo filter in SQL
        occ_notes = [Note.from_point_str(i, p) for i, p in zip(nids, points)]
        query_notes = [Note.from_point_str(i, p) for i, p in enumerate(query)]
        if occurrence.filter_occurrences(occ_notes, query_notes, occfilters):
            yield (pid, nids, points)

def search(query):
    m = set()
    notes = [Note.from_point_str(i, p) for i, p in enumerate(query)]
    for nw in NoteWindow.from_notes(-1, notes, len(notes)):
        results = plpy.execute(f"""
            SELECT * FROM search_sql_gin_exact('{nw.to_string()}')
        """)
        for r in results:
            m.add((r['pid'], tuple(r['nids']), tuple(r['notes'])))
    return m

def generate_notewindows(points, window_size, pid=-1):
    notes = [Note.from_point_str(i, p) for i, p in enumerate(points)]
    for nw in NoteWindow.from_notes(pid, notes, window_size):
        #yield (nw.pid, nw.notes[0].onset, nw.notes[-1].onset, nw.u.index, nw.v.index, [n.to_point() for n in nw.notes], [n.to_point() for n in nw.normalized_notes]) 
        yield {
            'pid': nw.pid,
            'u': nw.u.index,
            'v': nw.v.index,
            'onset_start': nw.notes[0].onset,
            'onset_end': nw.notes[-1].onset,
            'note_ids': [n.index for n in nw.notes],
            'unnormalized': [n.to_point() for n in nw.notes],
            'normalized': [n.to_point() for n in nw.normalized_notes]
        }

def generate_notevectors(points):
    for l, r in combinations(points, 2): 
        l_note = Note.from_point_str(-1, l)
        r_note = Note.from_point_str(-1, r)
        yield (r_note.onset - l_note.onset, r_note.pitch - l_note.pitch, l, r)

def generate_enumerated_notevectors(points):
    enumerated_points = list(enumerate(points))
    for (l_i, l), (r_i, r) in combinations(enumerated_points, 2): 
        l_note = Note.from_point_str(l_i, l)
        r_note = Note.from_point_str(r_i, r)
        yield (r_note.onset - l_note.onset, r_note.pitch - l_note.pitch, l_i, r_i)

