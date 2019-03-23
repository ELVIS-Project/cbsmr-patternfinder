class EmptyScoreError(Exception):
    """
    Thrown when music21 parses a score but finds 0 notes.
    """