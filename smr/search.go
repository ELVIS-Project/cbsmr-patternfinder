package main

/*
import (
	pb "../proto"
	"sort"
)

func Search(pieceMap map[PieceId]CScore, notes []Note) (occs []Occurrence, err error) {
	vecs := VecsFromNotes(notes)

	queryScore := InitScoreFromVectors(len(notes), vecs)

	for pieceId, cscore := range pieceMap {
		intArrays, err := search(queryScore, cscore)
		if err != nil {
			return nil, err
		}
		for _, arr := range intArrays {
			occs = append(occs, Occurrence{notes: arr, pid: pieceId})
		}
	}

	if len(occs) == 0 {
		return []Occurrence{}, nil
	}

	sortedOccs := rankTrivial(occs.Occurrences)
	sort.Sort(sortedOccs)

	return sortedOccs, nil
}
*/
