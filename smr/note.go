/** note.go
***
**/

package main

import (
	pb "../proto"
)

type NoteIndex int32

type Base40Type int32

type Note struct {
	Onset    float64 // absolute quarter length from beginning of piece
	Duration float64 // relative logarithm
	Pitch    Base40Type   // base 40
	Idx NoteIndex
}

func (n Note) toPbNote() (pbNote *pb.Note) {
	return &pb.Note{
		Onset: float32(n.Onset),
		//Duration:
		Pitch: (int32)(n.Pitch),
		PieceIdx: (uint32)(n.Idx),
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
		if left[k].Onset < right[k].Onset {
			return NOTES_LE
		} else if left[k].Onset > right[k].Onset {
			return NOTES_GE
		}
	}
	return NOTES_EQ
}

func (n Note) HashKey() (key Note) {
	return Note{
		Onset: n.Onset,
		Duration: n.Duration,
		Pitch: n.Pitch,
	}
}

func NewNote(protoNote *pb.Note, idx int) (n Note) {
	n.Onset = float64(protoNote.Onset)
	//n.Duration = math.Log2(float64(protoNote.Offset - protoNote.Onset))
	n.Pitch = Base40Type(protoNote.Pitch)
	n.Idx = NoteIndex(int32(idx))
	return
}

func NotesFromPbNotes(protoNotes []*pb.Note) []Note {
	notes := make([]Note, len(protoNotes))
	for i, pbNote := range protoNotes {
		notes[i] = NewNote(pbNote, i)
	}
	return notes
}

func PbNotesFromNotes(notes []Note) (protoNotes []*pb.Note) {
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
	if ns[i].Onset < ns[j].Onset {
		return true
	} else if ns[i].Onset == ns[j].Onset {
		return ns[i].Pitch < ns[j].Pitch
	} else {
		return false
	}
}
