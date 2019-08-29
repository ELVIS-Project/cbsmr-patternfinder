from dataclasses import dataclass
import indexers

@dataclass
class OccurrenceFilters:
    transpositions: list
    intervening: tuple
    inexact: tuple

def filter_occurrences(occurrences, query_pb_notes, requested_filters):
    return [occ for occ in occurrences if all((
        filter_by_transposition(query_pb_notes, occ, requested_filters.transpositions),
        filter_by_intervening(occ, requested_filters.intervening),
        filter_by_num_notes(query_pb_notes, occ, requested_filters.inexact)
        ))]

def filter_by_transposition(query_pb_notes, pb_occ, allowed_transpositions):
    actual = (query_pb_notes[0].pitch - pb_occ.notes[0].pitch) % 12
    return actual in allowed_transpositions

def filter_by_intervening(pb_occ, intervening):
    smallest_allowed, biggest_allowed = intervening
    skips = [y - x for x, y in zip((x.piece_idx for x in pb_occ.notes), (y.piece_idx for y in pb_occ.notes[1:]))]
    return min(skips) > smallest_allowed and max(skips) <= biggest_allowed + 1

def filter_by_num_notes(query_pb_notes, pb_occ, inexact):
    num_missing = len(query_pb_notes) - len(pb_occ.notes)
    return num_missing >= inexact[0] and num_missing <= inexact[1]
