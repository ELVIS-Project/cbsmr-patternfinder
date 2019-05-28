package main

import (
	"bytes"
	"encoding/gob"
)

type PieceId uint32

struct Piece {
	Notes []note
	Vectors []vector
	Pid PieceIdx
}

func (s Score) Encode() ([]byte, error) {
	buf := bytes.NewBuffer([]byte{})
	encoder := gob.NewEncoder(buf)
	err := encoder.Encode(s)
	if err != nil {
		return []byte{}, err
	}
	return buf.Bytes(), nil
}

func DecodeScore(input []byte) (s Score, err error) {
	buf := bytes.NewBuffer(input)
	decoder := gob.NewDecoder(buf)
	err = decoder.Decode(&s)
	if err != nil {
		return Score{}, err
	}
	return
}

