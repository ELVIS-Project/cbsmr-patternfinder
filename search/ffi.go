package main

import (
	pb "../proto"
	"unsafe"
)

// #cgo LDFLAGS: -L ./helsinki-ttwi/w2 -l w2
// #include "./helsinki-ttwi/w2/w2.h"
import "C"

const (
	WINDOW = 10
)

func min(a int, b int) (minimum int) {
	if a < b {
		return a
	}
	return b
}

func InitScoreFromCsv(vector_csv string) (score *C.struct_Score) {
	println((C.int)(len(vector_csv)))
	score = C.init_score_with_length((*C.char)(unsafe.Pointer(&vector_csv)), (C.int)(len(vector_csv)))
	return score
}

type NoteVector struct {
	a *pb.Note
	b *pb.Note
}

func VecsFromNotes(notes []*pb.Note) (vecs []NoteVector) {
	for i, _ := range notes {
		for j := i; j < min(i+WINDOW, len(notes)); j++ {
			vecs = append(vecs, NoteVector{notes[i], notes[j]})
		}
	}
	return
}

func InitScoreFromNotes(notes []*pb.Note) (C_score C.struct_Score) {
	var C_vecs []*C.struct_IntraVector
	vecs := VecsFromNotes(notes)
	for _, vec := range vecs {
		C_vecs = append(C_vecs, &C.struct_IntraVector{
			x:             (C.float)(vec.b.Onset - vec.a.Onset),
			y:             (C.int)(vec.b.PitchB40 - vec.b.PitchB40),
			startIndex:    (C.int)(vec.b.PitchB40 - vec.b.PitchB40),
			endIndex:      (C.int)(vec.b.PitchB40 - vec.b.PitchB40),
			diatonicDiff:  (C.int)(vec.b.PitchB40 - vec.b.PitchB40),
			chromaticDiff: (C.int)(vec.b.PitchB40 - vec.b.PitchB40),
		})
	}

	C_score = C.struct_Score{
		vectors:     (*C.struct_IntraVector)(unsafe.Pointer(&C_vecs)),
		num_notes:   (C.int)(len(notes)),
		num_vectors: (C.int)(len(vecs)),
	}

	return
}

func Search(pattern *C.struct_Score, target *C.struct_Score) (result *C.struct_Result) {
	_, retcode := C.search_return_chains(
		pattern,
		target,
		result,
	)

	if retcode != nil {
		panic("Search failed!")
	}

	return
}

/*
func twoCombinations(iterable interface{}) (combos [][]interface{}) {
	for i, a := range iterable {
		for j, b := range iterable {
			combos = append(combo, []interface{a, b})
		}
	}

}
*/
