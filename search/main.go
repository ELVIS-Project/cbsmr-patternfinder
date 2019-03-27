package main

import (
	indexer "../indexer"
	pb "../proto"
	"github.com/boltdb/bolt"
	"github.com/sirupsen/logrus"
	"google.golang.org/grpc"
	"io/ioutil"
	"os"
)

const (
	TESTPIECE = {"./test_data/lemstrom2011/leiermann.xml"}
	TESTQUERY = {"./test_data/lemstrom2011/query_a.mid"}
)

type SearchService struct{}

var db *bolt.DB

func (s SearchService) Search(req pb.SearchRequest) (*pb.SearchResponse, error) {
}

func indexTestPiece() indexer.IndexResponse {
	db, err := bolt.Open("./search.db", 0666)
	if err != nil {
		log.Panicln("Failed to open search database")
	}

	indexerClient, err := grpc.Dial("localhost:50051")
	if err != nil {
		log.Panicln("Failed to connect to indexer service")
	}

	pieceData, err := ioutil.ReadFile(TESTPIECE)
	if err != nil {
		log.Panicln("Failed to open test piece")
	}

	return indexerClient.IndexPiece(indexer.IndexRequest{piece: pieceData})
}

func main() {

	s := grpc.NewServer()
	pb.RegisterNewSearchService(s, &SearchService{})

	indexTestPiece()
}
