"""
smrpy/__init__.py

This package is intended to be run as a plpython3u extension in PostgreSQL
"""
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
from smrpy.hausdorf import generate_normalized_windows_with_notes
from smrpy.excerpt import coloured_excerpt

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
