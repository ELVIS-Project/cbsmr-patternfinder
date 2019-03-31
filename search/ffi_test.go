package main

import (
	pb "../proto"
	"context"
	"fmt"
	log "github.com/sirupsen/logrus"
	"google.golang.org/grpc"
	"io/ioutil"
	"testing"
)

func indexPieceFromDisk(path string) *pb.IndexResponse {

	println("Dialing indexer")
	conn, err := grpc.Dial("localhost:50051", grpc.WithInsecure())
	if err != nil {
		log.Panicf("Failed to connect to indexer service, %v", err)
	}
	indexerClient = pb.NewIndexerClient(conn)

	pieceData, err := ioutil.ReadFile(path)
	if err != nil {
		log.Panicln("Failed to open test piece")
	}

	piece := &pb.Piece{
		SymbolicData: pieceData,
	}

	resp, err := indexerClient.IndexPiece(context.Background(), &pb.IndexRequest{Piece: piece})
	if err != nil {
		log.Panicln("Failed to index grpc")
	}
	return resp
}

func TestLemstrom(t *testing.T) {

	leiermannIndexed := indexPieceFromDisk(TESTPIECE)
	queryIndexed := indexPieceFromDisk(TESTQUERY)

	query := InitScoreFromCsv(queryIndexed.VectorsCsv)
	leiermann := InitScoreFromCsv(leiermannIndexed.VectorsCsv)

	arrays := search(query, leiermann)

	println(fmt.Sprintf("%v", arrays))

	if fmt.Sprintf("%v", arrays) != "[[3 6 8 9 16 21] [13 14 16 17 18 21]]" {
		t.Fail()
	}
}
