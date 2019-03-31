package main

import (
	pb "../proto"
	"math"
	"sort"
)

const (
	windowSize = 30
)

var (
	bins = make(map[Note][]Basis)
)

type Basis struct {
	u Note
	v Note
}

type Note struct {
	onset    float64 // absolute quarter length from beginning of piece
	duration float64 // relative logarithm
	pitch    int32   // base 40
}

func NewNote(protoNote *pb.Note) (n Note) {
	n.onset = float64(protoNote.Onset)
	n.duration = math.Log2(float64(protoNote.Offset - protoNote.Onset))
	n.pitch = protoNote.PitchB40
	return
}

func toAlgNotes(resp *pb.IndexResponse) []Note {
	notes := make([]Note, len(resp.Notes))
	for i := range resp.Notes {
		notes[i] = NewNote(resp.Notes[i])
	}
	return notes
}

type byOnsetPitch []Note

func (ns byOnsetPitch) Len() int {
	return len(ns)
}
func (ns byOnsetPitch) Swap(i, j int) {
	ns[i], ns[j] = ns[j], ns[i]
}
func (ns byOnsetPitch) Less(i, j int) bool {
	return ns[i].onset <= ns[j].onset && ns[i].pitch < ns[j].pitch
}

type Window []Note

func NewWindow(notes []Note, idx int) (w Window) {
	slice := notes[idx:min(idx+windowSize, len(notes))]
	w = make([]Note, len(notes))

	for i := 0; i < len(slice); i++ {
		w[i] = slice[i]
	}
	return
}

func (w Window) Normalize(b Basis) Window {
	normalizedWindow := make(Window, len(w))
	for i, _ := range w {
		normalizedWindow[i].pitch = w[i].pitch - b.u.pitch
		normalizedWindow[i].onset = w[i].onset / math.Abs(b.v.onset)
		normalizedWindow[i].duration = w[i].duration
	}
	return normalizedWindow
}

func PreProcess(notes []Note) {
	sort.Sort(byOnsetPitch(notes))

	// :uncertain is it bad to take time window only forwards, not backwards?
	for i, u := range notes {
		window := NewWindow(notes, i)

		for _, v := range window {
			basis := Basis{u, v}
			nw := window.Normalize(basis)

			// skip the basis note `u'
			for _, note := range nw[1:] {
				bins[note] = append(bins[note], basis)
			}
		}
	}
}

func Query(notes []Note) (result [][]Note) {
	matchSet := make(map[Basis][]Note)

	sort.Sort(byOnsetPitch(notes))

	queryAsWindow := NewWindow(notes, 0)

	for i := range queryAsWindow {
		for j := i; j < len(queryAsWindow); j++ {
			basis := Basis{queryAsWindow[i], queryAsWindow[j]}
			nw := queryAsWindow.Normalize(basis)

			// skip the basis note
			for _, note := range nw[1:] {
				for _, b := range bins[note] {
					matchSet[b] = append(matchSet[b], note)
				}
			}
		}
	}

	for _, val := range matchSet {
		if len(val) == len(notes) {
			result = append(result, val)
		}
	}

	return
}
