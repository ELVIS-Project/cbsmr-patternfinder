package main

import (
	pb "../proto"
	"context"
	"fmt"
	"google.golang.org/grpc"
	"io/ioutil"
	"testing"
)

const (
	TESTPIECE = "./test_data/lemstrom2011/leiermann.xml"
	TESTQUERY = "./test_data/lemstrom2011/query_a.mid"
)

func rpanic(path string) []byte {
	data, err := ioutil.ReadFile(path)
	if err != nil {
		panic(err)
	}
	return data
}

func TestServiceWithLemstrom(t *testing.T) {
	server := StartServer()

	query := rpanic(TESTQUERY)
	target := InitScoreFromCsv(indexPieceFromDisk(TESTPIECE).VectorsCsv)

	pieceMap = map[uint32]CScore{0: target}

	conn, err := grpc.Dial("localhost:8080", grpc.WithInsecure())
	if err != nil {
		t.Errorf("Failed to dial searcher microservice")
	}
	searchClient := pb.NewSearcherClient(conn)

	println("Search request to server...")
	resp, err := searchClient.Search(context.Background(), &pb.SearchRequest{SymbolicData: query})
	if err != nil {
		panic(err)
	}

	if fmt.Sprintf("%v", resp.Occs[0].NoteIdx) != "[3 6 8 9 16 21]" {
		t.Fail()
	}
	if fmt.Sprintf("%v", resp.Occs[1].NoteIdx) != "[13 14 16 17 18 21]" {
		t.Fail()
	}
	server.GracefulStop()
}
