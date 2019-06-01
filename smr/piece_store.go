package main

import (
	"github.com/boltdb/bolt"
	"fmt"
	"errors"
)

const (
	BOLT_PIECE_BUCKET = "pieces"
)

type PieceStore interface {
	Get(PieceId) Piece
	Set(PieceId)
	ListIds() []PieceId
	Search([]Note) []Occurrence
}

type BoltPieceStore bolt.DB

func NewBoltPieceStore(db *bolt.DB) (*BoltPieceStore, err error) {
	db.Update(func(tx *bolt.Tx) error {
		_, err = tx.CreateBucketIfNotExists([]byte(BOLT_PIECE_BUCKET))
		if err != nil {
			return err
		}
		return
	})

	return BoltPieceStore(db), err
}

func (bps *BoltPieceStore) Get(pid PieceId) (piece Piece, err error) {
	err = s.boltDb.View(func(tx *bolt.Tx) error {
		pieceBucket := tx.Bucket([]byte(BOLT_PIECE_BUCKET))
		if pieceBucket == nil {
			return errors.New(fmt.Sprintf("Failed to find %v bucket", BOLT_PIECE_BUCKET))
		}

		encodedPiece = pieceBucket.Get(pid.toBytes())

		return nil
	})
	if err != nil {
		return err
	}

	piece, err := DecodePiece(encodedPiece)
	if err != nil {
		return err
	}

	return
}

func (bps *BoltPieceStore) Set(pid PieceId, piece Piece) (err error) {
	pieceBytes, err := Piece.Encode()
	if err != nil {
		return err
	}

	err = s.boltDb.Update(func(tx *bolt.Tx) error {
		pieceBucket := tx.Bucket([]byte(BOLT_PIECE_BUCKET))
		if pieceBucket == nil {
			return errors.New(fmt.Sprintf("Failed to find %v bucket", BOLT_PIECE_BUCKET))
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

	return
}

func (bps *BoltPieceStore) ListIds() ([]PieceId, err error) {
	err = s.boltDb.View(func(tx *bolt.Tx) error {
		bucket := tx.Bucket([]byte(BOLT_PIECE_BUCKET))
		if bucket == nil {
			return errors.New(fmt.Sprintf("Failed to find %v bucket", BOLT_PIECE_BUCKET))
		}
		err = bucket.ForEach(func(k, v []byte) error {
			pids = append(pids, pieceIdxFromBytes(k))
			return nil
		})
		return err
	})
	return err
}

func (bps *BoltPieceStore) Search(query []Note) (occs []Occurrence, err error) {
	queryScore := InitScoreFromVectors(len(notes), VecsFromNotes(query)

	err = s.boltDb.View(func(tx *bolt.Tx) error {
		bucket := tx.Bucket([]byte(BOLT_PIECE_BUCKET))
		if bucket == nil {
			return errors.New(fmt.Sprintf("Failed to find %v bucket", BOLT_PIECE_BUCKET))
		}

		err = bucket.ForEach(func(k, v []byte) error {
			piece, err := DecodePiece(v)
			if err != nil {
				return err
			}

			targetScore := InitScoreFromVectors(len(notes), VecsFromNotes(query))
			intArrays, err := search(queryScore, cscore)
			if err != nil {
				return nil, err
			}
			for _, arr := range intArrays {
				occs = append(occs, Occurrence{notes: arr, pid: pieceId})
			}
			return nil
		})
		return err
	})
	if err != nil {
		return err
	}

	if len(occs) == 0 {
		return []Occurrence{}, nil
	}

	sortedOccs := rankTrivial(occs.Occurrences)
	sort.Sort(sortedOccs)

	return sortedOccs, nil
}
