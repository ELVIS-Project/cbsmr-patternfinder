package main

import (
	"fmt"
	"testing"
)

func TestAlgorithmSimple(t *testing.T) {
	query := []Note{
		{onset: 0, duration: 1, pitch: 40},
		{onset: 1, duration: 1, pitch: 50},
	}

	target := []Note{
		{onset: 10, duration: 1, pitch: 40},
		{onset: 11, duration: 1, pitch: 50},
		{onset: 12, duration: 1, pitch: 50},
	}

	PreProcess(target)
	println(fmt.Sprintf("%v", bins))

	println(fmt.Sprintf("%v", Query(query)))

}

func TestAlgorithm(t *testing.T) {

	queryResp := indexPieceFromDisk(TESTQUERY)
	targetResp := indexPieceFromDisk(TESTPIECE)

	query := toAlgNotes(queryResp)
	target := toAlgNotes(targetResp)

	PreProcess(target)

	println(fmt.Sprintf("%v", bins))

	println(fmt.Sprintf("%v", Query(query)))
}
