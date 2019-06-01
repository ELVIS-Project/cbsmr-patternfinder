/** piece.go
***
**/

package main

import (
	"bytes"
	"encoding/gob"
	"encoding/binary"
)

type PieceId uint32

func (pid PieceId) toBytes() []byte {
	b := make([]byte, 8)
	binary.BigEndian.PutUint64(b, uint64(pid))
	return b
}

func (pid PieceId) toPbPieceId() uint32 {
	return uint32(pid)
}

func pieceIdFromBytes(v []byte) PieceId {
	return (PieceId)(binary.BigEndian.Uint64(v))
}

type Piece struct {
	Notes []Note
	Vectors []vector
	Pid PieceId
}

func (s Piece) Encode() ([]byte, error) {
	buf := bytes.NewBuffer([]byte{})
	encoder := gob.NewEncoder(buf)
	err := encoder.Encode(s)
	return buf.Bytes(), err
}

func DecodePiece(input []byte) (p Piece, err error) {
	buf := bytes.NewBuffer(input)
	decoder := gob.NewDecoder(buf)
	err = decoder.Decode(&p)
	return p, err
}
