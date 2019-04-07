package main

import (
	pb "../proto"
	"fmt"
	"math"
	"sort"
)

var (
	bins = make(map[Note][]Basis)
	windowSize = 2
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

func binsInit() {
	bins = make(map[Note][]Basis)
}

func printBins() {
	for note, bases := range bins {
		fmt.Printf("%v: %v\n", note, bases)
	}
}

func NewNote(protoNote *pb.Note) (n Note) {
	n.onset = float64(protoNote.Onset)
	n.duration = math.Log2(float64(protoNote.Offset - protoNote.Onset))
	n.pitch = protoNote.PitchB40
	return
}

func (n Note) Normalize(b Basis) (normedNote Note) {
	normedVOnset := b.v.onset - b.u.onset

	normedNote.pitch = n.pitch - b.u.pitch
	normedNote.onset = n.onset - b.u.onset
	normedNote.duration = n.duration - b.u.duration

	normedNote.onset /= math.Abs(normedVOnset)

	return
}
func (n Note) Denormalize(b Basis) (denormedNote Note) {
	normedVOnset := b.v.onset - b.u.onset
	denormedNote.onset = n.onset * math.Abs(normedVOnset)

	denormedNote.pitch = n.pitch + b.u.pitch
	denormedNote.onset += b.u.onset
	denormedNote.duration = n.duration + b.u.duration

	return
}

func toAlgNotes(resp *pb.Notes) []Note {
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


type Results [][]Note

func (rs Results) Len() int {
	return len(rs)
}
func (rs Results) Swap(i, j int) {
	rs[i], rs[j] = rs[j], rs[i]
}
func (rs Results) Less(i, j int) bool {
	for k := 0; k < min(len(rs[i]), len(rs[j])); k++ {
		if rs[i][k].onset < rs[j][k].onset { return true }
	}
	return false
}

/*
func (rs Results) ToNoteIndices(target []*pb.Note) (indices [][]uint32){
	for i, res := range rs {
		sort.Sort(res)
		for j, note := range res {
			k := sort.Search(len(target), func (i int) bool { return target[i] == note })
			indices[i][j] = target[k].PieceIdx
		}
	}
	return indices
}
*/


type Window []Note

func NewWindow(notes []Note, idx int) (w Window) {
	slice := notes[idx:min(idx+windowSize, len(notes))]
	w = make([]Note, len(slice))

	for i := 0; i < len(slice); i++ {
		w[i] = slice[i]
	}

	return
}

func (w Window) Normalize(b Basis) Window {
	normalizedWindow := make(Window, len(w))

	for i, _ := range w {
		normalizedWindow[i] = w[i].Normalize(b)
	}
	return normalizedWindow
}

func (w Window) Denormalize(b Basis) Window {
	denormalizedWindow := make(Window, len(w))

	for i, _ := range w {
		denormalizedWindow[i] = w[i].Denormalize(b)
	}
	return denormalizedWindow
}

func PreProcess(notes []Note) {
	sort.Sort(byOnsetPitch(notes))

	//println(fmt.Sprintf("Notes: %v", notes))
	// :uncertain is it bad to take time window only forwards, not backwards?
	for i, u := range notes {
		//print("Processing window centered at ", i)
		window := NewWindow(notes, i)
		//println(fmt.Sprintf("	%v", window))

		// skip the basis note `u'
		for _, v := range window[1:] {
			basis := Basis{u, v}
			//println("Normalizing with basis: ", fmt.Sprintf("%v", basis))

			nw := window.Normalize(basis)

			//println(fmt.Sprintf("	%v", nw))

			for _, note := range nw {
				bins[note] = append(bins[note], basis)
			}
		}
	}
}

func Query(notes []Note) (results Results) {
	matchSet := make(map[Basis][]Note)

	sort.Sort(byOnsetPitch(notes))

	queryAsWindow := NewWindow(notes, 0)

	for i := range queryAsWindow {
		for j := i + 1; j < len(queryAsWindow); j++ {
			basis := Basis{queryAsWindow[i], queryAsWindow[j]}
			//println("query considering basis %v", fmt.Sprintf("%v", basis))
			nw := queryAsWindow.Normalize(basis)
			//println("query normalized: %v", fmt.Sprintf("%v", nw))

			for _, note := range nw {
				for _, basis := range bins[note] {

					alreadyExists:= false
					for _, n := range matchSet[basis] {
						if n == note { alreadyExists = true }
					}
					if !alreadyExists {
						matchSet[basis] = append(matchSet[basis], note)
					}

				}
			}
		}
	}

	//println("\nMATCH SET")
	//for basis, notes := range matchSet {
		//println(fmt.Sprintf("%v: %v", basis, notes))
	//}

	for basis, notes := range matchSet {
		if len(notes) > 1 {
			for i := range notes {
				notes[i] = notes[i].Denormalize(basis)
			}
			sort.Sort(byOnsetPitch(notes))
			results = append(results, notes)
		}
	}
	sort.Sort(results)

	return
}
