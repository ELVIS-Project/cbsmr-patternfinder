package main

import (
	"github.com/boltdb/bolt"
	"encoding/asn1"
)

func (s *SmrServer) LoadScores(window int) error {

	err := s.boltDb.View(func(tx *bolt.Tx) error {
		scoreBucket := tx.Bucket([]byte("scores"))
		err := scoreBucket.ForEach(func(k, v []byte) error {

			score := Score{}
			_, err := asn1.Unmarshal(v, &score)
			if err != nil {
				return err
			}

			for i := range score.Vectors {
				if (int)(score.Vectors[i].EndIndex - score.Vectors[i].StartIndex) > window {
					score.Vectors = append(score.Vectors[:i], score.Vectors[i+1:]...)
				}
			}

			s.pieceMap[btoi(k)] = InitScoreFromVectors(score.NumNotes, score.Vectors)
			return nil
		})

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

