package main
/*

import (
	pb "../proto"
	"context"
	"github.com/boltdb/bolt"
	"encoding/binary"
	"errors"
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

	vecs := VecsFromNotes(&pb.Notes{Notes: req.Notes})
	score := Score{
		Vectors: vecs,
		NumNotes: len(req.Notes),
	}

	scoreBytes, err := score.Encode()
	if err != nil {
		return nil, err
	}

	err = s.boltDb.Update(func(tx *bolt.Tx) error {
		scoreBucket := tx.Bucket([]byte("scores"))
		if scoreBucket == nil {
			return errors.New("Can't retrieve 'scores' bucket")
		}
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

	// :todo make a LoadScore()
	s.LoadOneScore(req.Id, WINDOW)

	println("Put in a score! id: ", req.Id)
	return &pb.AddPieceResponse{Id: id}, nil
}

func (s *SmrServer) AllPieces(ctx context.Context, req *pb.AllPiecesRequest) (resp *pb.AllPiecesResponse, err error) {
	var pids []uint32
	err = s.boltDb.View(func(tx *bolt.Tx) error {
		bucket := tx.Bucket([]byte("scores"))
		if bucket == nil {
			return errors.New("Can't retrieve 'scores' bucket")
		}
		bucket.ForEach(func(k, v []byte) error {
			pids = append(pids, btoi(k))
			return nil
		})
		return nil
	})
	if err != nil {
		return nil, err
	}
	return &pb.AllPiecesResponse{Pids: pids}, nil
}
*/
