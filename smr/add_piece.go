package main

import (
	pb "../proto"
	"context"
	"github.com/boltdb/bolt"
	"encoding/binary"
)

func itob(v uint32) []byte {
	b := make([]byte, 8)
	binary.BigEndian.PutUint64(b, uint64(v))
	return b
}

func btoi(v []byte) uint32 {
	return (uint32)(binary.BigEndian.Uint64(v))
}

func (s *SmrServer) AddPiece(ctx context.Context, req *pb.AddPieceRequest) (resp *pb.AddPieceResponse, err error) {
	var id uint32

	vecs := VecsFromNotes(req.Notes)
	score := Score{
		Vectors: vecs,
		NumNotes: len(req.Notes.Notes),
	}

	scoreBytes, err := score.Encode()
	if err != nil {
		return nil, err
	}

	err = s.boltDb.Update(func(tx *bolt.Tx) error {
		scoreBucket := tx.Bucket([]byte("scores"))
		err := scoreBucket.Put(itob(req.Id), scoreBytes)
		if err != nil {
			return err
		}
		id = req.Id
		return nil
	})

	if err != nil {
		return nil, err
	}

	return &pb.AddPieceResponse{Id: id}, nil
}
