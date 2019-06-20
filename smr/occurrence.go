/** occurrence.go
***
**/

package main

import (
	pb "../proto"
)

type Occurrence struct {
	notes []Note
	pid PieceId
}

func (occ Occurrence) toPbOcc() *pb.Occurrence {
	return &pb.Occurrence{Notes: PbNotesFromNotes(occ.notes), Pid: occ.pid.toPbPieceId()}
}

type rankOccurrencesTrivial []Occurrence

func (occs rankOccurrencesTrivial) Len() int {
	return len(occs)
}
func (occs rankOccurrencesTrivial) Swap(i, j int) {
	occs[i], occs[j] = occs[j], occs[i]
}
func (occs rankOccurrencesTrivial) Less(i, j int) bool {
	// Most relevant come first
	if len(occs[i].notes) < len(occs[j].notes)  {
		return true
	} else if len(occs[i].notes) > len(occs[j].notes) {
		return false
	}

	// now len(occs[i].Notes) == len(occs[j].Notes)
	var sum_i NoteIndex
	var sum_j NoteIndex
	for k := 1; k < len(occs[i].notes); k++ {
		sum_i += occs[i].notes[k].Idx - occs[i].notes[k-1].Idx
		sum_j += occs[j].notes[k].Idx - occs[j].notes[k-1].Idx
	}

	// Prefer more compact occurrences
	if sum_i > sum_j {
		return true
	} else if sum_i < sum_j {
		return false
	} else {
		// If all else equal, sort on piece id for deterministic results
		return occs[i].pid < occs[j].pid
	}
}
