package main

import (
	"testing"
	"bytes"
	"fmt"
)

func TestBoltPieceStoreStaticDataEntryAndRetrieval(t *testing.T) {
	var err error

	notes := []Note{
		Note{Onset: 0, Duration: 1, Pitch: 162, Idx: NoteIndex(0)},
		Note{1, 1, 168, NoteIndex(1)},
		Note{1, 1, 174, NoteIndex(2)},
	}
	vectors := VecsFromNotes(notes, len(notes))
	piece := Piece{
		Notes: notes,
		Vectors: vectors,
		Pid: PieceId(0),
	}
	db := testOpenBolt()
	defer closeBolt()
	store, err := NewBoltPieceStore(db)
	if err != nil {
		t.Errorf("failed on NewBoltPieceStore: %v", err)
	}

	err = store.Set(PieceId(0), piece)
	if err != nil {
		t.Errorf("failed on setting piece id 0: %v", err)
	}

	gotPiece, err := store.Get(PieceId(0))
	if err != nil {
		t.Errorf("failed on getting piece id 0: %v", err)
	}

	expected, err := piece.Encode()
	xk(err)
	got, err := gotPiece.Encode()
	xk(err)
	if !bytes.Equal(got, expected) {
		t.Error("piece retrieved is not identical to the one we inserted")
	}
}

func TestBoltPieceStoreSearchLemstrom(t *testing.T) {
	var err error
	db := testOpenBolt()
	defer closeBolt()
	store, err := NewBoltPieceStore(db)
	xk(err)

	leiermannPiece := NewPieceFromFile(LEIERMANN + ".idxresp_notes", 0)
	query := UnmarshalNotesFromFile(LEIERMANN_QUERY[0] + ".idxresp_notes")

	err = store.Set(0, leiermannPiece)
	xk(err)

	occs, err := store.Search(query)
	if err != nil {
		t.Errorf("%v", err)
	}

	var filteredOccs []Occurrence
	for i := range occs {
		if len(occs[i].notes) == 6 {
			filteredOccs = append(filteredOccs, occs[i])
		}
	}

	expected := "[{[{3 0 112 13} {3.5 0 123 14} {4 0 118 16} {4.5 0 95 17} {5 0 118 18} {6 0 112 21}] 0} {[{0 0 112 3} {1.5 0 123 6} {2 0 118 8} {3 0 95 11} {4 0 118 16} {6 0 112 21}] 0} {[{3 0 112 13} {3.5 0 123 14} {4 0 118 16} {4.5 0 95 17} {5 0 118 18} {8.5 0 112 31}] 0} {[{3 0 112 13} {3.5 0 123 14} {5 0 118 18} {6 0 95 20} {8 0 118 29} {8.5 0 112 31}] 0} {[{0 0 112 3} {1.5 0 123 6} {2 0 118 8} {3 0 95 11} {4 0 118 16} {8.5 0 112 31}] 0}]"
	if fmt.Sprintf("%v", filteredOccs) != expected {
		t.Errorf("expected %v got %v", expected, occs)
	}
}
