/** note.go
***
**/

package main

import (
	pb "../proto"
)

type Note struct {
	onset    float64 // absolute quarter length from beginning of piece
	duration float64 // relative logarithm
	pitch    int32   // base 40
	idx int32
}

func (n Note) toPbNote() (pbNote *pb.Note) {
	return &pb.Note{
		Onset: float32(n.onset),
		//Duration:
		PitchB40: n.pitch,
		PieceIdx: (uint32)(n.idx),
	}
}

type NotesCmp int

const (
	NOTES_LE NotesCmp = iota
	NOTES_EQ
	NOTES_GE
)

func CmpNotesByOnset(left []Note, right []Note) NotesCmp {
	if len(left) < len(right) {
		return NOTES_LE
	} else if len(left) > len(right) {
		return NOTES_GE
	}

	for k := 0; k < len(left); k++ {
		if left[k].onset < right[k].onset {
			return NOTES_LE
		} else if left[k].onset > right[k].onset {
			return NOTES_GE
		}
	}
	return NOTES_EQ
}

func (n Note) HashKey() (key Note) {
	return Note{
		onset: n.onset,
		duration: n.duration,
		pitch: n.pitch,
	}
}

func NewNote(protoNote *pb.Note, idx int) (n Note) {
	n.onset = float64(protoNote.Onset)
	//n.duration = math.Log2(float64(protoNote.Offset - protoNote.Onset))
	n.pitch = int32(protoNote.PitchB40)
	n.idx = int32(idx)
	return
}

func NotesFromPbNotes(protoNotes []*pb.Note) ([]Note) {
	notes := make([]Note, len(protoNotes))
	for i, pbNote := range protoNotes {
		notes[i] = NewNote(pbNote, i)
	}
	return notes
}

func PbNotesFromNotes(notes []Note) (protoNotes []*pb.Note) {
	protoNotes = make([]*pb.Note, len(notes))
	for _, note := range notes {
		protoNotes = append(protoNotes, note.toPbNote())
	}
	return
}

type byOnsetPitch []Note

func (ns byOnsetPitch) Len() int {
	return len(ns)
}
func (ns byOnsetPitch) Swap(i, j int) {
	ns[i], ns[j] = ns[j], ns[i]
}
func (ns byOnsetPitch) Less(i, j int) bool {
	if ns[i].onset < ns[j].onset {
		return true
	} else if ns[i].onset == ns[j].onset {
		return ns[i].pitch < ns[j].pitch
	} else {
		return false
	}
}

