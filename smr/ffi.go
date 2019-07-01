/** w2_ffi.go
***
*** This calls into the C-lang w2 library to utilize the search algorithm from golang
**/

package main

import (
	"fmt"
	"sort"
	"unsafe"
	"errors"
)

// #cgo LDFLAGS: -L ./helsinki-ttwi/build -l w2
// #include "./helsinki-ttwi/w2.h"
import "C"

type CScore *C.Score

func PrintScore(s *C.Score) {
	println(fmt.Sprintf("Score with %v notes and %v vecs:", s.num_notes, s.num_vectors))
	vecs := (*[1 << 30]C.IntraVector)(unsafe.Pointer(s.vectors))
	for i := 0; (C.int)(i) < s.num_vectors; i++ {
		cv := vecs[i]
		println(fmt.Sprintf("x: %v, y: %v, si: %v, ei; %v", cv.x, cv.y, cv.startIndex, cv.endIndex))
	}
}

type vector struct {
	X          float64
	Y          Base40Type
	StartIndex NoteIndex
	EndIndex   NoteIndex
}

type byHeightThenIndex []vector

func (vs byHeightThenIndex) Len() int {
	return len(vs)
}
func (vs byHeightThenIndex) Swap(i, j int) {
	vs[i], vs[j] = vs[j], vs[i]
}
func (vs byHeightThenIndex) Less(i, j int) bool {
	if vs[i].Y < vs[j].Y {
		return true
	} else if vs[i].Y == vs[j].Y {
		return vs[i].StartIndex <= vs[j].StartIndex
	} else {
		return false
	}
}

func VecsFromNotes(notes []Note, window int) (vecs []vector) {

	for i, _ := range notes {
		for j := i + 1; j < min(i + 1 + window, len(notes)); j++ {
			cvec := vector{
				(float64)(notes[j].Onset - notes[i].Onset),
				Base40Type(notes[j].Pitch - notes[i].Pitch),
				notes[i].Idx,
				notes[j].Idx,
			}
			vecs = append(vecs, cvec)
		}
	}

	sortedVecs := byHeightThenIndex(vecs)
	sort.Sort(sortedVecs)
	return sortedVecs
}

func InitScoreFromVectors(numNotes int, vecs []vector) (s CScore) {
	CVectors := (*C.IntraVector)(C.malloc(C.sizeof_IntraVector * (C.ulong)(len(vecs))))
	GoCVectors := (*[1 << 30]C.IntraVector)(unsafe.Pointer(CVectors))
	for i, v := range vecs {
		CVec := (C.IntraVector)(C.NewIntraVector(
			(C.float)(v.X),
			(C.int)(v.Y),
			(C.int)(v.StartIndex),
			(C.int)(v.EndIndex),
		))

		GoCVectors[i] = CVec
	}

	s = C.InitScoreFromVectors(
		(C.int)(numNotes), (C.int)(len(vecs)),
		CVectors,
	)
	return
}

func CSearch(pattern CScore, target CScore) (arrays [][]uint32, err error) {
	if pattern.num_notes < 2 {
		return arrays, errors.New("pattern must be at least two notes long")
	}

	/*
	KLists := (*C.KTableLinkedList)(C.malloc((C.ulong)(pattern.num_notes - 1) * C.sizeof_KTableLinkedList))
	KTables := (*C.KTable)(C.malloc((C.ulong)(pattern.num_notes) * C.sizeof_KTable))
	println("init")
	C.InitKTables(KTables, KLists, pattern, target)
	println("algorihtm")
	C.algorithm(KTables, KLists, pattern, target)
	result := (*C.ResultList)(C.malloc(C.sizeof_ResultList))
	println("extract")
	C.extract_chains(KTables, KLists, pattern, target, result)
	*/

	result := c_search(pattern, target)

	arrays = resultToIntArrays(result)
	return arrays, nil
}

func c_search(pattern *C.Score, target *C.Score) (resultList *C.ResultList) {
	resultList = C.search(
		(*C.Score)(unsafe.Pointer(pattern)),
		(*C.Score)(unsafe.Pointer(target)),
	)
	return
}

func resultToIntArrays(resultList *C.ResultList) (arrays [][]uint32) {

	curResult := (*C.ResultListNode)(unsafe.Pointer(resultList.head))
	for i := 0; (C.int)(i) < resultList.length; i++ {
		chain := (*[1 << 10]C.int)(unsafe.Pointer(curResult.chain))
		arr := make([]uint32, curResult.length)

		for j := 0; (C.int)(j) < curResult.length; j++ {
			arr[j] = (uint32)(chain[j])
		}
		arrays = append(arrays, arr)
		curResult = curResult.next
	}

	return
}
