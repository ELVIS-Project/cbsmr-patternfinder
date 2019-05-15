package main

import (
	"testing"
	"io/ioutil"
	"path"
)

func TestSearchPalestrina(t *testing.T) {
	var err error
	var pieceMap = make(map[uint32]CScore)
	files, err := ioutil.ReadDir(path.Join(PALESTRINA, "pb_notes"))
	xk(err)

	query := UnmarshalNotesFromFile(path.Join(PALESTRINA, "double_leading_tone_query.pb_notes"))
	for i, file := range files {
		target := InitScoreFromFile(path.Join(PALESTRINA, "pb_notes", file.Name()))
		pieceMap[(uint32)(i)] = target
	}

	occs, err := Search(pieceMap, query)
	if err != nil {
		t.Errorf("%v", err)
	}

	if len(occs.Occurrences) < 23 {
		t.Errorf("not enough occurrences")
	}
	/*
	for i := range occs.Occurrences[:23] {
		fmt.Printf("%v: %v\n", files[occs.Occurrences[i].Pid], occs.Occurrences[i])
	}
	*/
}


