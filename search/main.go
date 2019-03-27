package main

import (
	pb "../proto"
	"context"
	"github.com/boltdb/bolt"
	log "github.com/sirupsen/logrus"
	"google.golang.org/grpc"
	"io/ioutil"
	"time"
)

const (
	TESTPIECE = "./test_data/lemstrom2011/leiermann.xml"
	TESTQUERY = "./test_data/lemstrom2011/query_a.mid"
)

type SearchServer struct{}

var db *bolt.DB

func (s SearchServer) Search(ctx context.Context, req *pb.SearchRequest) (*pb.SearchResponse, error) {
	var resp pb.SearchResponse
	return &resp, nil
}

func indexTestPiece() *pb.IndexResponse {
	_, err := bolt.Open("./search.db", 0666, &bolt.Options{Timeout: 1 * time.Second})
	if err != nil {
		log.Panicln("Failed to open search database")
	}

	conn, err := grpc.Dial("localhost:50051")
	if err != nil {
		log.Panicln("Failed to connect to indexer service")
	}
	indexerClient := pb.NewIndexerClient(conn)

	pieceData, err := ioutil.ReadFile(TESTPIECE)
	if err != nil {
		log.Panicln("Failed to open test piece")
	}

	piece := &pb.Piece{
		SymbolicData: pieceData,
		Encoding:     "xml",
		Name:         "leiermann",
	}

	resp, err := indexerClient.IndexPiece(context.Background(), &pb.IndexRequest{Piece: piece})
	if err != nil {
		log.Panicln("Failed to index grpc")
	}
	return resp
}

func main() {

	s := grpc.NewServer()
	pb.RegisterSearchServiceServer(s, &SearchServer{})

	indexTestPiece()
}
