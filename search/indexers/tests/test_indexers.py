import pytest
import pkg_resources
import indexers
import pandas as pd

def test_notes():
    with pkg_resources.resource_stream("indexers", "tests/leiermann.xml") as f:
        symbolic_data = f.read()

    with pkg_resources.resource_stream("indexers", "tests/leiermann.notes") as f:
        notes_expected = pd.read_csv(f)
    
    notes_actual = indexers.notes(symbolic_data)

    assert notes_actual.equals(notes_expected)

def test_intra_vectors():
    with pkg_resources.resource_stream("indexers", "tests/leiermann.xml") as f:
        symbolic_data = f.read()

    with pkg_resources.resource_stream("indexers", "tests/leiermann.intra_vectors") as f:
        intra_vectors_expected = pd.read_csv(f)
    
    intra_vectors_actual = indexers.intra_vectors(symbolic_data)

    assert intra_vectors_actual.equals(intra_vectors_expected)