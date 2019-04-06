package main

import (
	pb "../proto"
	"context"
	"io/ioutil"
	"path"
	//"strconv"
	//"strings"
)

const (
	ELVISDUMP = "/Users/davidgarfinkle/elvis-project/elvisdump"
)

var (
	TESTPALESTRINA = []string{
		"./testdata/palestrina_masses/000000000011125_Missa-Hodie-christus-natus-est_Sanctus_Palestrina-Giovanni-Pierluigi-da_file2.mid",
		"./testdata/palestrina_masses/000000000011344_Missa-Primi-toni_Credo_Palestrina-Giovanni-Pierluigi-da_file2.mid",
	}
)

func loadScores() {

	_, err := ioutil.ReadDir(path.Join(ELVISDUMP, "XML"))
	if err != nil {
		panic(err)
	}

	for i, p := range TESTPALESTRINA {
		data, err := ioutil.ReadFile(p)
		if err != nil {
			panic(err)
		}
		indexed, err := indexerClient.IndexPiece(context.Background(), &pb.IndexRequest{
			Piece: &pb.Piece{SymbolicData: data},
		})
		if err != nil {
			panic(err)
		}
		score := InitScoreFromIndexerResp(indexed)
		pieceMap[(uint32)(i)] = score
	}
	/*
		for _, file := range files[:5] {
			println("Loading score ", file.Name())
			data, err = ioutil.ReadFile(path.Join(ELVISDUMP, "XML", file.Name()))
			indexed, err := indexerClient.IndexPiece(context.Background(), &pb.IndexRequest{
				Piece: &pb.Piece{SymbolicData: data},
			})
			if err != nil {
				panic(err)
			}
			score := InitScoreFromIndexerResp(indexed)

			identifier, err := strconv.ParseUint(strings.Split(path.Base(file.Name()), "_")[0], 10, 32)
			if err != nil {
				panic(err)
			}
			pieceMap[(uint32)(identifier)] = score
		}
	*/
}
