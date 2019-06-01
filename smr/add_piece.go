package main
/*

import (
	pb "../proto"
	"context"
	"github.com/boltdb/bolt"
	"errors"
	log "github.com/sirupsen/logrus"
)

func AddPiece(piece Piece) (err error) {

	pieceBytes, err := Piece.Encode()
	if err != nil {
		return err
	}

	err = s.boltDb.Update(func(tx *bolt.Tx) error {
		pieceBucket := tx.Bucket([]byte("pieces"))
		if pieceBucket == nil {
			return errors.New("Can't retrieve 'pieces' bucket")
		}
		err := pieceBucket.Put(piece.pid.toBytes(), pieceBytes)
		if err != nil {
			return err
		}
		return nil
	})
	if err != nil {
		return err
	}

	return nil
}

func GetPieceIds(bolt bolt.DB) (pids []PieceId, err error) {
	err = s.boltDb.View(func(tx *bolt.Tx) error {
		bucket := tx.Bucket([]byte("pieces"))
		if bucket == nil {
			return errors.New("Can't retrieve 'pieces' bucket")
		}
		bucket.ForEach(func(k, v []byte) error {
			pids = append(pids, pieceIdxFromBytes(k))
			return nil
		})
		return nil
	})
	return
}
*/
