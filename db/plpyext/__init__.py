"""
smrpy/__init__.py

This package is intended to be run as a plpython3u extension in PostgreSQL
"""
import base64
import music21
import xml.etree.ElementTree as ET
import io
from itertools import groupby
from smrpy import piece, indexers

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

def symbolic_data_to_m21_xml(sd_b64):
    sd = base64.b64decode(sd_b64)
    xml = piece.symbolic_data_to_m21_xml(sd)
    return xml

def excerpt(m21_xml, nids, measure_start, measure_end, color='#FF0000'):
    stream = music21.converter.parse(m21_xml)
    excerpt = stream.measures(numberStart=measure_start, numberEnd=measure_end)
    m21_xml_excerpt = piece.m21_score_to_xml_write(excerpt)
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
    parts = list(st.parts)
    nps = indexers.NotePointSet(st)
    for i, n in enumerate(nps):
        yield {
            'pid': -1,
            'n': piece.Note.from_m21(n, i).to_point(),
            'nid': i,
            'part_id': f"{parts.index(n.original_part)}-{n.original_part.partName}"
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

def swap_iter(it):
    for left, right in it:
        yield right, left

"""
pid  |   p_notes   |   t_notes   | t_nids  
-------+-------------+-------------+---------
 10919 | {1,10,1,14} | {0,55,0,59} | {0,1}
"""

def search(p_nids, t_nids, len_pattern, threshold):
    from plpyext import lemstrom_search
    return lemstrom_search.search(p_nids, t_nids, len_pattern, threshold)
"""
Grouped vecs as
    SELECT
        pid,
        MIN(p_notes ORDER BY t_notes ASC) AS p_notes,
        MIN(t_notes ORDER BY t_notes ASC) AS t_notes
    FROM vecs
    GROUP BY (pid, p_notes[1:2], t_notes[1:2])
"""

"""
    vec_dict = {(pid, p_bind, t_bind): (p_vecs, t_vecs) for pid, p_bind, t_bind, p_vecs, t_vecs in zip(pids, p_binds, t_binds, p_vecs, t_vecs)}
    for i in range(4):
        for pid, p_vec, t_vec in zip(pids, p_vecs, t_vecs):
            key = (pid, p_vec[1:2], t_vec[1:2])
            if vec_dict.get(key)
                vec_dict[key] = vec_dict.get(key) + (p_vec[3:4], t_vec[3:4])
"""
