package main

import (
	"fmt"
	"testing"
)

func TestAlgorithmSimpleCases(t *testing.T) {
	windowSize = 2

	testCases := []struct {
		window int
		query []Note
		target []Note
		result string
	}{
		{
			// Two occurrences, unscaled
			2,
			[]Note {
				{onset: 0, duration: 1, pitch: 10},
				{onset: 2, duration: 1, pitch: 20},
			},
			[]Note {
				{onset: 0, duration: 1, pitch: 10},
				{onset: 2, duration: 1, pitch: 20},
				{onset: 4, duration: 1, pitch: 30},
			},
			"[[{0 1 10} {2 1 20}] [{2 1 20} {4 1 30}]]",
		},
		{
			// One occurrence, scaled
			2,
			[]Note {
				{onset: 0, duration: 1, pitch: 10},
				{onset: 2, duration: 1, pitch: 20},
			},
			[]Note {
				{onset: 0, duration: 2, pitch: 10},
				{onset: 4, duration: 2, pitch: 20},
			},
			"[[{0 2 10} {4 2 20}]]",
		},
		{
			// Two occurrences, one is scaled
			2,
			[]Note {
				{onset: 0, duration: 1, pitch: 10},
				{onset: 2, duration: 1, pitch: 20},
			},
			[]Note {
				{onset: 0, duration: 2, pitch: 10},
				{onset: 4, duration: 2, pitch: 20},
				{onset: 8, duration: 1, pitch: 10},
				{onset: 10, duration: 1, pitch: 20},
			},
			"[[{0 2 10} {4 2 20}] [{8 1 10} {10 1 20}]]",
		},
		{
			// Two occurrences, one is scaled, embedded within larger score
			3,
			[]Note {
				{onset: 0, duration: 1, pitch: 10},
				{onset: 2, duration: 1, pitch: 20},
				{onset: 4, duration: 1, pitch: 50},
			},
			[]Note {
				{onset: 0, duration: 0, pitch: 20},
				{onset: 1, duration: 0, pitch: 20},
				{onset: 2, duration: 0, pitch: 20},
				{onset: 3, duration: 0, pitch: 20},
				{onset: 4, duration: 1, pitch: 20},
				{onset: 6, duration: 1, pitch: 30},
				{onset: 8, duration: 1, pitch: 60},
				{onset: 10, duration: 0, pitch: 40},
				{onset: 11, duration: 0, pitch: 40},
				{onset: 12, duration: 2, pitch: 20},
				{onset: 16, duration: 2, pitch: 30},
				{onset: 20, duration: 2, pitch: 60},
			},
			"[[{4 1 20} {6 1 30} {8 6 40}] [{12 2 20} {16 2 30} {20 2 40}]]",
		},
	}

	for _, test := range testCases {
		fmt.Printf("Testing query %v against target %v\n with window %v", test.query, test.target, test.window)

		windowSize = test.window

		binsInit()

		PreProcess(test.target)

		res := fmt.Sprintf("%v", Query(test.query))

		//println("\nBINS")
		//printBins()

		if res != test.result {
			println("Failed, got ", res)
			t.FailNow()
		}
	}
}

func TestAlgorithmLemstrom(t *testing.T) {
	windowSize=9

	queryResp := indexPieceFromDisk(TESTQUERY)
	targetResp := indexPieceFromDisk(TESTPIECE)

	query := toAlgNotes(queryResp)
	target := toAlgNotes(targetResp)

	println("\n QUERY")
	for i := range query {
		fmt.Printf("%v %v: %v\n", i, queryResp.Notes[i], query[i])
	}
	println("\n TARGET")
	for i := range target {
		fmt.Printf("%v %v: %v\n", i, targetResp.Notes[i], target[i])
	}

	PreProcess(target)

	res := Query(query)
	//resNotes := res.ToNoteIndices(targetResp.Notes)

	for _, notes := range res {
		if len(notes) < 4 { continue }
		fmt.Printf("%v\n", notes)
		//fmt.Printf("%v\n", resNotes[i])
	}
}

func TestNormalize(t *testing.T) {
	target := []Note{
		{onset: 0, duration: 1, pitch: 10},
		{onset: 2, duration: 1, pitch: 20},
		{onset: 4, duration: 1, pitch: 30},
	}
	window := Window(target)
	nw := window.Normalize(Basis{target[0], target[1]})
	if fmt.Sprintf("%v", nw) != "[{0 0 0} {1 0 10} {2 0 20}]" {
		t.Fail()
	}
}

func TestDenormalize(t *testing.T) {
	target := []Note{
		{onset: 0, duration: 1, pitch: 10},
		{onset: 2, duration: 1, pitch: 20},
		{onset: 4, duration: 1, pitch: 30},
	}
	basis := Basis{target[0], target[1]}
	window := Window(target)
	nw := window.Normalize(basis)
	dw := nw.Denormalize(basis)

	// Round trip
	if len(nw) != len(dw) { t.Fail() }
	for i, _ := range nw {
		if window[i] != dw[i] {
			t.Fail()
		}
	}
}
