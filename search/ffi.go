package main

import (
	pb "../proto"
	"fmt"
	"sort"
	"unsafe"
)

// #cgo LDFLAGS: -L ./helsinki-ttwi/w2 -l w2
// #include "./helsinki-ttwi/w2/w2.h"
import "C"

const (
	WINDOW = 10
)

type CScore *C.struct_Score

func PrintScore(s *C.struct_Score) {
	println(fmt.Sprintf("Score with %v notes and %v vecs:", s.num_notes, s.num_vectors))
	vecs := (*[1 << 30]C.struct_IntraVector)(unsafe.Pointer(s.vectors))
	for i := 0; (C.int)(i) < s.num_vectors; i++ {
		cv := vecs[i]
		println(fmt.Sprintf("x: %v, y: %v, si: %v, ei; %v", cv.x, cv.y, cv.startIndex, cv.endIndex))
	}
}

type vector struct {
	x          float32
	y          int32
	startIndex uint32
	endIndex   uint32
}

type byHeightThenIndex []vector

func (vs byHeightThenIndex) Len() int {
	return len(vs)
}
func (vs byHeightThenIndex) Swap(i, j int) {
	vs[i], vs[j] = vs[j], vs[i]
}
func (vs byHeightThenIndex) Less(i, j int) bool {
	if vs[i].y < vs[j].y {
		return true
	} else if vs[i].y == vs[j].y {
		return vs[i].startIndex <= vs[j].startIndex
	} else {
		return false
	}
}

func VecsFromNotes(notes []*pb.Note) (vecs []vector) {
	sort.Sort(byHeightThenIndex(vecs))
	for i, _ := range notes {
		for j := i; j < min(i+WINDOW, len(notes)); j++ {
			cvec := vector{
				notes[j].Onset - notes[i].Onset,
				notes[j].PitchB40 - notes[i].PitchB40,
				notes[i].PieceIdx,
				notes[j].PieceIdx,
			}
			vecs = append(vecs, cvec)
		}
	}
	return
}

func InitScoreFromVectors(numNotes int, vecs []vector) (s CScore) {
	CVectors := (*C.struct_IntraVector)(C.malloc(C.sizeof_struct_IntraVector * (C.ulong)(len(vecs))))
	GoCVectors := (*[1 << 30]C.struct_IntraVector)(unsafe.Pointer(CVectors))
	for i, v := range vecs {
		CVec := (C.struct_IntraVector)(C.NewIntraVector(
			(C.float)(v.x),
			(C.int)(v.y),
			(C.int)(v.startIndex),
			(C.int)(v.endIndex),
		))

		GoCVectors[i] = CVec
	}

	s = C.initScoreFromVectors(
		(C.int)(numNotes), (C.int)(len(vecs)),
		CVectors,
	)
	return
}

func min(a int, b int) (minimum int) {
	if a < b {
		return a
	}
	return b
}

func search(pattern CScore, target CScore) (arrays [][]uint32) {

	result := CSearch(pattern, target)

	return resultToIntArrays(result, pattern)
}

func InitScoreFromCsv(vector_csv string) (score *C.struct_Score) {
	score = C.init_score(C.CString(vector_csv))
	return score
}

func CSearch(pattern *C.struct_Score, target *C.struct_Score) (result *C.struct_Result) {
	result = (*C.struct_Result)(C.malloc(C.sizeof_struct_Result))
	C.search(
		(*C.struct_Score)(unsafe.Pointer(pattern)),
		(*C.struct_Score)(unsafe.Pointer(target)),
		(*C.struct_Result)(unsafe.Pointer(result)),
	)
	return
}

func resultToIntArrays(result *C.struct_Result, pattern *C.struct_Score) (arrays [][]uint32) {

	chains := (*[1 << 30]*C.int)(unsafe.Pointer(result.chains))
	println(result.num_occs)
	for i := 0; (C.int)(i) < result.num_occs; i++ {
		// weird.. can't cast a pointer to a larger array with variable size at compile time?
		chain := (*[1 << 10]C.int)(unsafe.Pointer(chains[i]))
		arr := make([]uint32, pattern.num_notes)

		for j := 0; (C.int)(j) < pattern.num_notes; j++ {
			arr[j] = (uint32)(chain[j])
			if chain[j] == 0 {
				break
			}
		}

		arrays = append(arrays, arr)
	}

	return
}

/*
func recurseChain(kEntry *C.struct_KEntry) []*C.struct_IntraVector {
	if kEntry.y == nil {
		return [2]*C.struct_IntraVector{kEntry.targetVec.startIndex, kEntry.targetVec.endIndex}
	} else {
		return append(recurseChain(KEntry.y), [1]*C.struct_IntraVector{KEntry.targetVec.endIndex})
	}
}
func kTableToOccurrence(result *C.struct_Result, kTableLength int) pb.Occurrence {
	chains := [][]C.struct_IntraVector{}
	table := ([]*C.struct_KEntry)(result.table)

	for i := 0; i < kTableLength; i++ {
		if result.table[i].w > 0 {
			chains = append(chains, recursively_extract_chain(KTable[i]))
		}
	}

	return chains
}

func twoCombinations(iterable interface{}) (combos [][]interface{}) {
	for i, a := range iterable {
		for j, b := range iterable {
			combos = append(combo, []interface{a, b})
		}
	}

}

func (vec NoteVector) toIntArray() (arr [8]int) {
	arr[0] = (C.float)(vec.b.Onset - vec.a.Onset)
	arr[1] = (C.int)(vec.b.PitchB40 - vec.a.PitchB40)
	arr[2] = (C.int)(vec.a.pieceIdx)
	arr[3] = (C.int)(vec.b.pieceIdx)
	arr[4] = (C.int)(vec.a.PitchB40)
	arr[5] = (C.int)(vec.b.PitchB40)
	arr[6] = (C.int)(arr[0])
	arr[7] = (C.int)(arr[0])
}

func vecsToIntArray(vecs []NoteVector) (arr []int) {
	arr = make([]int, len(vecs)*8)
	for i, vec := range vecs {
		println("%v", i)
		vecArray := vec.toIntArray()
		for i := 0; i < 8; i++ {
			arr[i] = vecArray[i]
		}
		println("%v", arr)
	}
	return
}

func InitScoreWithIntArray(notes []*pb.Note) (C_score *C.struct_Score) {
	vecs := VecsFromNotes(notes)
	vecsAsIntArray := vecsToIntArray(vecs)
	C_score = C.init_score_from_int_array((C.int)(len(notes)), (C.int)(len(vecs)), (*C.int)(unsafe.Pointer(&vecsAsIntArray)))
}

func InitScoreFromNotes(notes []*pb.Note) (C_score *C.struct_Score) {
	var C_vecs []*C.struct_IntraVector
	vecs := VecsFromNotes(notes)

	//mc_vecs := (*C.struct_IntraVector)(C.malloc(C.size_t(len(vecs))))
	//mc_vecs_ptrs := (*[]C.struct_IntraVector)(unsafe.Pointer(mc_vecs))[:len(vecs):len(vecs)]

	for _, vec := range vecs {
		//mc_vec := (C.struct_IntraVector)(C.malloc(C.sizeof_struct_IntraVector))
		/*
			C_vecs = append(C_vecs, &C.struct_IntraVector{
				x:             (C.float)(vec.b.Onset - vec.a.Onset),
				y:             (C.int)(vec.b.PitchB40 - vec.b.PitchB40),
				startIndex:    (C.int)(vec.b.PitchB40 - vec.b.PitchB40),
				endIndex:      (C.int)(vec.b.PitchB40 - vec.b.PitchB40),
				diatonicDiff:  (C.int)(vec.b.PitchB40 - vec.b.PitchB40),
				chromaticDiff: (C.int)(vec.b.PitchB40 - vec.b.PitchB40),
			})
		x := (C.float)(vec.b.Onset - vec.a.Onset)
		y := (C.int)(vec.b.PitchB40 - vec.a.PitchB40)
		sI := (C.int)(vec.a.PieceIdx)
		eI := (C.int)(vec.b.PieceIdx)
		sP := (C.int)(vec.a.PitchB40)
		eP := (C.int)(vec.b.PitchB40)
		dD := (C.int)(y)
		cD := (C.int)(y)
		C_vecs = append(C_vecs, C.NewIntraVector(x, y, sI, eI, sP, eP, dD, cD))
	}

	println("init score")
	C_score = C.init_score_from_vectors(
		(C.int)(len(notes)),
		(C.int)(len(vecs)),
		(*C.struct_IntraVector)(unsafe.Pointer(&C_vecs[0])),
	)
		C_score = (*C.struct_Score)(C.malloc(C.sizeof_struct_Score))
		C_score = &C.struct_Score{
			vectors:     (*C.struct_IntraVector)(unsafe.Pointer(&C_vecs[0])),
			num_notes:   (C.int)(len(notes)),
			num_vectors: (C.int)(len(vecs)),
		}

	return
}


type NoteVector struct {
	a *pb.Note
	b *pb.Note
}

*/
