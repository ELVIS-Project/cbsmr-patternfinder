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

	arrays, err := search(query, leiermann)
	if err != nil {
		t.Errorf("%v", err)
	}

	expected := "[[3 6 8 9 16 21] [13 14 16 17 18 21] [13 14 16 17 18 31]]"
	if fmt.Sprintf("%v", arrays) != expected {
		t.Errorf("expected %v got %v", expected, arrays)
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

			arr, err := search(query, target)
			if err != nil {
				t.Errorf("%v", err)
			}

			arr2, err := search(query, target)
			if err != nil {
				t.Errorf("%v", err)
			}

			// Find something
			if len(arr) == 0 {
				t.Errorf("found nothing in %v", file)
			}

			// Should be sorted
			if len(arr) != len(arr2) {
				t.Errorf("two invocations of search got different lists");
			}
			for i := range arr {
				for j := range arr[i] {
					if arr[i][j] != arr2[i][j] {
						t.Errorf("two invocations of search are in different orders");
					}
				}
			}
		})
	}
}

func Test457(t *testing.T) {
	target := InitScoreFromFile("testdata/000000000000457_Castigans-castigavit_Josquin-Des-Prez_file3.xml")
	queryNotes := UnmarshalNotesFromFile("testdata/queries/" + "DA_F.pb_notes")
	queryVecs := VecsFromNotes(queryNotes)
	query := InitScoreFromVectors(len(queryNotes.Notes), queryVecs)

	_, err := search(query, target)
	if err != nil {
		t.Errorf("%v", err)
	}
}
