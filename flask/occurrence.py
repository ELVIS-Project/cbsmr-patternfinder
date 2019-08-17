from dataclasses import dataclass
from indexer import indexers

@dataclass
class OccurrenceFilters:
    transpositions: list
    intervening: int

def filter_occurrences(occurrences, query_pb_notes, requested_filters):
    return [occ for occ in occurrences if all((
        filter_by_transposition(query_pb_notes, occ, requested_filters.transpositions),
        filter_by_intervening(occ, requested_filters.intervening)
        ))]

def filter_by_transposition(query_pb_notes, pb_occ, allowed_transpositions):
    actual = (query_pb_notes[0].pitch - pb_occ.notes[0].pitch) % 12
    return actual in allowed_transpositions

def filter_by_intervening(pb_occ, intervening):
    biggest_skip = max(y - x for x, y in zip((x.piece_idx for x in pb_occ.notes), (y.piece_idx for y in pb_occ.notes[1:])))
    return intervening >= biggest_skip - 1
