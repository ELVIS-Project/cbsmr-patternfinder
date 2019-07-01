package main

/*
import (
	"github.com/boltdb/bolt"
	"errors"
	vp "github.com/spf13/viper"
)

func (s *SmrServer) LoadOneScore(pid PieceId, window int) (err error) {
	piece := s.pieceStore.Get(pid)

	for i := range piece.Vectors {
		if (int)(piece.Vectors[i].EndIndex - piece.Vectors[i].StartIndex) > window {
			piece.Vectors = append(piece.Vectors[:i], piece.Vectors[i+1:]...)
		}
	}

	s.pieceMap[pid] = InitScoreFromVectors(piece.NumNotes, piece.Vectors)
	return nil
}

func (s *SmrServer) LoadScores(window int) (err error) {
	println("Loading Scores into memory!")

	ids, err := s.pieceStore.ListIds()
	if err != nil {
		return err
	}

	loaded := 0
	for i, id := range ids {
		if (i < vp.GetInt("SMR_MAX_SCORES")) {
			err = s.LoadOneScore(id, window)
		}
		if err != nil {
			loaded = loaded + 1
		}
	}
	println("Loaded ", loaded, " scores")

	return err
*/
