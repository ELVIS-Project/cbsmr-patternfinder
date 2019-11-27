import sys
import ast
from dataclasses import dataclass
from smrpy.piece import Note
from smrpy import smr_pb2, indexers

@dataclass
class OccurrenceFilters:
    transpositions: list
    intervening: tuple
    inexact: tuple

def sort_key(occ):
    return (
        len(occ),
        sum(y.index - x.index for x, y in zip(occ, occ[1:]))
    )

def filter_occurrences(occ, query_notes, requested_filters):
    return all((
        filter_by_transposition(query_notes, occ, requested_filters.transpositions),
        filter_by_intervening([n.index for n in occ], requested_filters.intervening),
        filter_by_num_notes(query_notes, occ, requested_filters.inexact),
        ))

def filter_by_transposition(query_notes, occ_notes, allowed_transpositions):
    actual = abs(query_notes[0].pitch - occ_notes[0].pitch) % 12
    return actual in allowed_transpositions

def filter_by_intervening(occ_nids, intervening):
    smallest_allowed, biggest_allowed = intervening
    skips = [y - x for x, y in zip(occ_nids, occ_nids[1:])]
    return min(skips) > smallest_allowed and max(skips) <= biggest_allowed + 1

def filter_by_num_notes(query_notes, occ_notes, inexact):
    num_missing = len(query_notes) - len(occ_notes)
    return num_missing >= inexact[0] and num_missing <= inexact[1]

def notes_from_points(inp):
    tuple_list = map(lambda string_tuple: ast.literal_eval(string_tuple), inp)
    return [Note(p[0], None, p[1], i) for i, p in enumerate(tuple_list)]

def occ_to_occpb(occ):
    notes = [note.to_pb(-1) for note in zip(notes_from_points(occ["notes"]))]
    return smr_pb2.Occurrence(pid=occ["pid"], notes=notes)
