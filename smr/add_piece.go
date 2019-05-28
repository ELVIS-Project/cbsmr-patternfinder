package main

import (
	pb "../proto"
	"context"
	"github.com/boltdb/bolt"
	"encoding/binary"
	"errors"
	log "github.com/sirupsen/logrus"
)

func itob(v uint32) []byte {
	b := make([]byte, 8)
	binary.BigEndian.PutUint64(b, uint64(v))
	return b
}

func btoi(v []byte) uint32 {
	return (uint32)(binary.BigEndian.Uint64(v))
}

func AddPiece(pid int, notes []*pb.Note) (err error) {

	vecs := VecsFromNotes(notes)
	score := Piece {
		Notes: notes
		Vectors: vecs,
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
		return nil
	})
	if err != nil {
		return nil, err
	}

	s.LoadOneScore(pid, WINDOW)

	log.Infoln("Put in a score! id: ", pid)
	return &pb.AddPieceResponse{}, nil
}

func GetPieceIds(bolt bolt.DB) (pids []uint32, err error) {
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
	return
}
