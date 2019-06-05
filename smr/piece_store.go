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

type InspectableStore interface {
	ListIds() []PieceId
}

type SearchableStore interface {
	Search([]Note) []Occurrence
}

type PieceStore interface {
	Get(PieceId) Piece
	Set(PieceId, Piece)
	SearchableStore
	InspectableStore
}

type BoltPieceStore struct {
	*bolt.DB
}

func NewBoltPieceStore(db *bolt.DB) (bps *BoltPieceStore, err error) {
	err = db.Update(func(tx *bolt.Tx) error {
		_, err = tx.CreateBucketIfNotExists([]byte(BOLT_PIECE_BUCKET))
		return err
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
			println(piece.Pid)

			// Search
			targetScore := InitScoreFromVectors(len(piece.Notes), VecsFromNotes(piece.Notes))
			intArrays, err := CSearch(queryScore, targetScore)
			if err != nil {
				return err
			}

			// Prepare occurrences
			for _, arr := range intArrays {
				println(fmt.Sprintf("%v", arr))
				var notes []Note
				for _, idx := range arr {
					n := piece.Notes[idx]
					n.Idx = NoteIndex(idx)
					notes = append(notes, n)
				}
				occs = append(occs, Occurrence{notes: notes, pid: piece.Pid})
			}
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

	sort.Sort(sort.Reverse(rankOccurrencesTrivial(occs)))

	return occs, nil
}

type CScoreStore interface {
	Get(PieceId) CScore
	Set(PieceId, CScore)
	SearchableStore
	InspectableStore
}

type MapCScoreStore map[PieceId]CScore

func (m MapCScoreStore) Get(pid PieceId) CScore {
	return m[pid]
}

func (m MapCScoreStore) Set(pid PieceId, score CScore) {
	m[pid] = score
}

func (m MapCScoreStore) ListIds() (pids []PieceId) {
	pids = make([]PieceId, len(m))
	for k := range m {
		pids = append(pids, k)
	}
	return pids
}

func (m MapCScoreStore) Search(query []Note) (occs []Occurrence, err error) {
	queryScore := InitScoreFromVectors(len(query), VecsFromNotes(query))

	for k, targetScore := range m {
		intArrays, err := CSearch(queryScore, targetScore)
		if err != nil {
			return nil, err
		}

		for _, arr := range intArrays {
			notes := make([]Note, len(arr))
			for _, x := range arr {
				notes = append(notes, Note{Idx: NoteIndex(x)})
			}
			occs = append(occs, Occurrence{notes: notes, pid: k})
		}
	}
	return
}
