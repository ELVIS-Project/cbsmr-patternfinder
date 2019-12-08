import sys
import ast
from dataclasses import dataclass
from smrpy.piece import Note
from smrpy import indexers

@dataclass
class OccurrenceFilters:
    transpositions: list
    intervening: tuple
    inexact: tuple

def filter_occurrences(occurrences, query_pb_notes, requested_filters):
    return [occ for occ in occurrences if all((
        #filter_by_transposition(query_pb_notes, occ, requested_filters.transpositions),
        #filter_by_intervening(occ, requested_filters.intervening),
        filter_by_num_notes(query_pb_notes, occ, requested_filters.inexact),
        ))]

def filter_by_transposition(query_notes, occ, allowed_transpositions):
    actual = (query_notes[0].pitch - occ.notes[0].pitch) % 12
    return actual in allowed_transpositions

def filter_by_intervening(pb_occ, intervening):
    smallest_allowed, biggest_allowed = intervening
    skips = [y - x for x, y in zip((x.piece_idx for x in pb_occ.notes), (y.piece_idx for y in pb_occ.notes[1:]))]
    return min(skips) > smallest_allowed and max(skips) <= biggest_allowed + 1

def filter_by_num_notes(query_pb_notes, pb_occ, inexact):
    num_missing = len(query_pb_notes) - len(pb_occ.notes)
    return num_missing >= inexact[0] and num_missing <= inexact[1]

def notes_from_points(inp):
    tuple_list = map(lambda string_tuple: ast.literal_eval(string_tuple), inp)
    return [Note(p[0], None, p[1], i) for i, p in enumerate(tuple_list)]
