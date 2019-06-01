package main

import (
	"testing"
	"bytes"
)

func TestBoltPieceStoreStaticDataEntryAndRetrieval(t *testing.T) {
	var err error

	notes := []Note{
		Note{Onset: 0, Duration: 1, Pitch: 162, Idx: NoteIndex(0)},
		Note{1, 1, 168, NoteIndex(1)},
		Note{1, 1, 174, NoteIndex(2)},
	}
	vectors := VecsFromNotes(notes)
	piece := Piece{
		Notes: notes,
		Vectors: vectors,
		Pid: PieceId(0),
	}
	store, err := NewBoltPieceStore(BOLT)
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
