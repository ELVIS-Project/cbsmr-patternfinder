package main

import (
	pb "../proto"
	"context"
	"database/sql"
	"github.com/boltdb/bolt"
	_ "github.com/lib/pq"
	log "github.com/sirupsen/logrus"
	"google.golang.org/grpc"
	"io/ioutil"
	"time"
)

const (
	TESTPIECE = "./test_data/lemstrom2011/leiermann.xml"
	TESTQUERY = "./test_data/lemstrom2011/query_a.mid"
	DBSTRING  = "host=localhost port=5432 user=postgres password=postgres sslmode=disable"
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
	pb.RegisterSearcherServer(s, &SearchServer{})

	db, err := sql.Open("postgres", DBSTRING)
	if err != nil {
		panic(err)
	}
	defer db.Close()
	if err = db.Ping(); err != nil {
		panic(err)
	}

}
