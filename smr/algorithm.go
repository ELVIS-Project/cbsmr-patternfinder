/** Romming's Geometric Hashing Retrieval Algorithm
*** :ref http://ismir2007.ismir.net/proceedings/ISMIR2007_p457_romming.pdf
*** 
*** Base40 Pitch Representation
*** :ref http://wiki.ccarh.org/wiki/Base_40
*** :ref http://www.ccarh.org/publications/reprints/base40/
**/

package main

import (
	pb "../proto"
	"fmt"
	//log "github.com/sirupsen/logrus"
	"math"
	"sort"
)

var (
	bins = make(map[Note][]Basis)
)

type Basis struct {
	u Note
	v Note
}


func binsInit() {
	bins = make(map[Note][]Basis)
}

func printBins() {
	for note, bases := range bins {
		fmt.Printf("%v: %v\n", note, bases)
	}
}

func (n Note) Normalize(b Basis) (normedNote Note) {
	normedVOnset := b.v.onset - b.u.onset

	normedNote.pitch = n.pitch - b.u.pitch
	normedNote.onset = n.onset - b.u.onset
	//normedNote.duration = n.duration - b.u.duration

	normedNote.onset /= math.Abs(normedVOnset)

	return
}
func (n Note) Denormalize(b Basis) (denormedNote Note) {
	normedVOnset := b.v.onset - b.u.onset
	denormedNote.onset = n.onset * math.Abs(normedVOnset)

	denormedNote.pitch = n.pitch + b.u.pitch
	denormedNote.onset += b.u.onset
	//denormedNote.duration = n.duration + b.u.duration

	return
}


type Results [][]Note

func (rs Results) Len() int {
	return len(rs)
}
func (rs Results) Swap(i, j int) {
	rs[i], rs[j] = rs[j], rs[i]
}
func (rs Results) Less(i, j int) bool {
	return CmpNotesByOnset(rs[i], rs[j]) == NOTES_LE
}


/*
func (rs Results) asNoteIndices(target []*pb.Note) (indices [][]uint32){
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

func (rs Results) toNoteIndices() (indices [][]int32) {
	indices = make([][]int32, len(rs))
	for i, result := range rs {
		indices[i] = make([]int32, len(result))
		for _, note := range result {
			indices[i] = append(indices[i], note.idx)
		}
	}
	return
}


type Window []Note

func NewWindow(notes []Note, idx int, windowSize int) (w Window) {
	slice := notes[idx:min(idx + windowSize, len(notes))]
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

func PreProcess(notes []Note, windowSize int) {
	sort.Sort(byOnsetPitch(notes))

	//println(fmt.Sprintf("Notes: %v", notes))
	// :uncertain is it bad to take time window only forwards, not backwards?
	for i, u := range notes {
		//println("Processing window centered at ", i)
		window := NewWindow(notes, i, windowSize)
		//println(fmt.Sprintf("	%v", window))

		// skip the basis note `u'
		for _, v := range window[1:] {
			basis := Basis{u, v}
			//println("Normalizing with basis: ", fmt.Sprintf("%v", basis))

			nw := window.Normalize(basis)

			//println(fmt.Sprintf("	%v", nw))

			for _, note := range nw {
				bins[note.HashKey()] = append(bins[note.HashKey()], basis)
			}
		}
	}
}

func Query(notes []Note, windowSize int) (results Results) {
	/*
	** MatchSet: What target scalings (bases) correspond to this particular query scaling?
	*/

	sort.Sort(byOnsetPitch(notes))

	queryAsWindow := NewWindow(notes, 0, windowSize)

	for i := range queryAsWindow {
		for j := i + 1; j < len(queryAsWindow); j++ {
			matchSet := make(map[Basis][]Note)
			basis := Basis{queryAsWindow[i], queryAsWindow[j]}
			//println("query considering basis %v", fmt.Sprintf("%v", basis))
			nw := queryAsWindow.Normalize(basis)
			//println("query normalized: %v", fmt.Sprintf("%v", nw))

			for _, note := range nw {
				for _, basis := range bins[note.HashKey()] {

					alreadyExists:= false
					for _, n := range matchSet[basis] {
						if n == note { alreadyExists = true }
					}
					if !alreadyExists {
						matchSet[basis] = append(matchSet[basis], note)
					}

				}
			}

			println("\nMATCH SET")
			for basis, notes := range matchSet {
				println(fmt.Sprintf("%v: %v", basis, notes))
			}

			for basis, notes := range matchSet {
				if len(notes) > 1 {
					for i := range notes {
						notes[i] = notes[i].Denormalize(basis)
					}
					sortedNotes := byOnsetPitch(notes)
					sort.Sort(sortedNotes)

					possiblyExists := sort.Search(len(results), func (i int) bool { return CmpNotesByOnset(results[i], sortedNotes) != NOTES_LE })
					fmt.Printf("%v got search idx %v in results list %v", sortedNotes, possiblyExists, results)

					if possiblyExists == len(results) {
						results = append(results, sortedNotes)
					}
				}
			}
		}
	}
	sort.Sort(results)

	//remove duplicates
	for i := range results {
		for j := range results {
			if !results.Less(i, j) && !results.Less(j, i) {
				//fmt.Printf("%v, %v, len %v", i, j, len(results))
				//fmt.Printf("%v, %v", results[:0], results[1:])
				/*
				if j < len(results) - 1 {
					results = append(results[:j], results[j+1:]...)
				}
				*/
			}
		}
	}

	return
}
