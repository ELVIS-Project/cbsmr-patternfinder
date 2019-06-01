package main

import (
	"github.com/boltdb/bolt"
	"fmt"
	"errors"
	"sort"
)

const (
	BOLT_PIECE_BUCKET = "pieces"
)

type PieceStore interface {
	Get(PieceId) Piece
	Set(PieceId, Piece)
	ListIds() []PieceId
	Search([]Note) []Occurrence
}

type BoltPieceStore struct {
	*bolt.DB
}

func NewBoltPieceStore(db *bolt.DB) (bps *BoltPieceStore, err error) {
	err = db.Update(func(tx *bolt.Tx) error {
		_, err = tx.CreateBucketIfNotExists([]byte(BOLT_PIECE_BUCKET))
		if err != nil {
			return err
		}
		return nil
	})
	if err != nil {
		return
	}

	bps = &BoltPieceStore {
		DB: db,
	}
	return
}

func (bps *BoltPieceStore) Get(pid PieceId) (piece Piece, err error) {
	var encodedPiece []byte

	err = bps.View(func(tx *bolt.Tx) error {
		pieceBucket := tx.Bucket([]byte(BOLT_PIECE_BUCKET))
		if pieceBucket == nil {
			return errors.New(fmt.Sprintf("Failed to find %v bucket", BOLT_PIECE_BUCKET))
		}

		encodedPiece = pieceBucket.Get(pid.toBytes())

		return nil
	})
	if err != nil {
		return
	}

	piece, err = DecodePiece(encodedPiece)
	return
}

func (bps *BoltPieceStore) Set(pid PieceId, piece Piece) (err error) {
	pieceBytes, err := Piece.Encode(piece)
	if err != nil {
		return
	}

	err = bps.Update(func(tx *bolt.Tx) error {
		pieceBucket := tx.Bucket([]byte(BOLT_PIECE_BUCKET))
		if pieceBucket == nil {
			return errors.New(fmt.Sprintf("Failed to find %v bucket", BOLT_PIECE_BUCKET))
		}
		err := pieceBucket.Put(piece.Pid.toBytes(), pieceBytes)
		return err
	})
	return
}

func (bps *BoltPieceStore) ListIds() (pids []PieceId, err error) {
	err = bps.View(func(tx *bolt.Tx) error {
		bucket := tx.Bucket([]byte(BOLT_PIECE_BUCKET))
		if bucket == nil {
			return errors.New(fmt.Sprintf("Failed to find %v bucket", BOLT_PIECE_BUCKET))
		}
		err = bucket.ForEach(func(k, v []byte) error {
			pids = append(pids, pieceIdFromBytes(k))
			return nil
		})
		return err
	})
	return
}

func (bps *BoltPieceStore) Search(query []Note) (occs []Occurrence, err error) {
	queryScore := InitScoreFromVectors(len(query), VecsFromNotes(query))

	err = bps.View(func(tx *bolt.Tx) error {
		bucket := tx.Bucket([]byte(BOLT_PIECE_BUCKET))
		if bucket == nil {
			return errors.New(fmt.Sprintf("Failed to find %v bucket", BOLT_PIECE_BUCKET))
		}

		err = bucket.ForEach(func(k, v []byte) error {
			piece, err := DecodePiece(v)
			if err != nil {
				return err
			}

			// Search
			targetScore := InitScoreFromVectors(len(piece.Notes), VecsFromNotes(query))
			intArrays, err := search(queryScore, targetScore)
			if err != nil {
				return err
			}

			// Prepare occurrences
			for _, arr := range intArrays {
				notes := make([]Note, len(arr))
				for i := range arr {
					notes = append(notes, piece.Notes[i])
				}
				occs = append(occs, Occurrence{notes: notes, pid: piece.Pid}) }
			return nil
		})
		return err
	})
	if err != nil {
		return
	}

	if len(occs) == 0 {
		return []Occurrence{}, nil
	}

	sortedOccs := rankOccurrencesTrivial(occs)
	sort.Sort(sortedOccs)

	return sortedOccs, nil
}
