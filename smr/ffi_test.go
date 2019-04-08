package main

import (
	"fmt"
	"testing"
	"io/ioutil"
	"path"
)

func TestLemstrom(t *testing.T) {

	query := InitScoreFromFile(LEIERMANN_QUERY[0] + ".pb_notes")
	leiermann := InitScoreFromFile(LEIERMANN + ".pb_notes")

	arrays := search(query, leiermann)

	if fmt.Sprintf("%v", arrays) != "[[3 6 8 9 16 21] [13 14 16 17 18 21]]" {
		t.Fail()
	}
}

func TestPalestrina(t *testing.T) {
	var err error
	files, err := ioutil.ReadDir(path.Join(PALESTRINA, "pb_notes"))
	xk(err)

	for _, file := range files {
		t.Run(file.Name(), func(t *testing.T) {
			targetNotes := UnmarshalNotesFromFile(path.Join(PALESTRINA, "pb_notes", file.Name()))
			targetVecs := VecsFromNotes(targetNotes)
			target := InitScoreFromVectors(len(targetNotes.Notes), targetVecs)

			queryNotes := UnmarshalNotesFromFile(path.Join(PALESTRINA, "double_leading_tone_query.pb_notes"))
			queryVecs := VecsFromNotes(queryNotes)
			query := InitScoreFromVectors(len(queryNotes.Notes), queryVecs)

			arr := search(query, target)

			if len(arr) == 0 {
				t.Errorf("found nothing in %v", file)
			}
		})
	}
}
