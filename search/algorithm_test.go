package main

import (
	"fmt"
	"testing"
)

func TestAlgorithmSimple(t *testing.T) {
	query := []Note{
		{onset: 0, duration: 1, pitch: 10},
		{onset: 2, duration: 1, pitch: 20},
	}

	target := []Note{
		{onset: 0, duration: 1, pitch: 10},
		{onset: 2, duration: 1, pitch: 20},
		{onset: 4, duration: 1, pitch: 30},
	}

	PreProcess(target)

	res := Query(query)
	if fmt.Sprintf("%v", res) != "[[{0 1 10} {2 1 20}] [{2 1 20} {4 1 30}]]" {
		t.Fail()
	}
}

func TestAlgorithmCases(t *testing.T) {
	testCases := []struct {
		query []Note
		target []Note
		result string
	}{
		{
			// Two occurrences, unscaled
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
	}

	for _, test := range testCases {
		binsInit()
		PreProcess(test.target)
		res := Query(test.query)
		if fmt.Sprintf("%v", res) != test.result {
			t.Fail()
		}
	}
}

func TestAlgorithmLemstrom(t *testing.T) {

	queryResp := indexPieceFromDisk(TESTQUERY)
	targetResp := indexPieceFromDisk(TESTPIECE)

	query := toAlgNotes(queryResp)
	target := toAlgNotes(targetResp)

	PreProcess(target)

	res := Query(query)

	println(fmt.Sprintf("%v", res))
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
