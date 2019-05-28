package main

import (
	"github.com/boltdb/bolt"
	"errors"
	vp "github.com/spf13/viper"
)

func (s *SmrServer) GetScoreIds() (ids []uint32, err error) {
	err = s.boltDb.View(func(tx *bolt.Tx) error {
		bucket := tx.Bucket([]byte("scores"))
		if bucket == nil {
			return errors.New("Failed to find 'scores' bucket")
		}
		bucket.ForEach(func(k, v []byte) error {
			ids = append(ids, btoi(k))
			return nil
		})
		return nil
	})

	if err != nil {
		return
	}

	return
}


func (s *SmrServer) LoadOneScore(pid uint32, window int) (err error) {
	var encodedScore []byte

	err = s.boltDb.View(func(tx *bolt.Tx) error {
		scoreBucket := tx.Bucket([]byte("scores"))
		if scoreBucket == nil {
			return errors.New("Failed to find 'scores' bucket")
		}

		encodedScore = scoreBucket.Get(itob(pid))

		return nil
	})

	if err != nil {
		return err
	}

	score, err := DecodeScore(encodedScore)
	if err != nil {
		return err
	}

	for i := range score.Vectors {
		if (int)(score.Vectors[i].EndIndex - score.Vectors[i].StartIndex) > window {
			score.Vectors = append(score.Vectors[:i], score.Vectors[i+1:]...)
		}
	}

	s.pieceMap[pid] = InitScoreFromVectors(score.NumNotes, score.Vectors)
	return nil
}

func (s *SmrServer) LoadScores(window int) error {
	println("Loading Scores into memory!")

	ids, err := s.GetScoreIds()
	if err != nil {
		return err
	}

	for i, id := range ids {
		if (i < vp.GetInt("SMR_MAX_SCORES")) {
			s.LoadOneScore(id, window)
		}
	}
	println("Loaded ", min(len(ids), vp.GetInt("SMR_MAX_SCORES")), " scores")

	return nil
}
