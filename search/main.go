package main

import (
	pb "../proto"
	"context"
	"database/sql"
	"fmt"
	"github.com/boltdb/bolt"
	_ "github.com/lib/pq"
	log "github.com/sirupsen/logrus"
	"google.golang.org/grpc"
	"io/ioutil"
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

func indexPieceFromDisk(path string) *pb.IndexResponse {
	/*
		_, err := bolt.Open("./search.db", 0666, &bolt.Options{Timeout: 1 * time.Second})
		if err != nil {
			log.Panicln("Failed to open search database")
		}
	*/

	conn, err := grpc.Dial("localhost:50051", grpc.WithInsecure())
	if err != nil {
		log.Panicf("Failed to connect to indexer service, %v", err)
	}
	indexerClient := pb.NewIndexerClient(conn)

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

func main() {

	s := grpc.NewServer()
	pb.RegisterSearcherServer(s, &SearchServer{})

	println("Opening connection")
	db, err := sql.Open("postgres", DBSTRING)
	if err != nil {
		panic(err)
	}
	defer db.Close()
	if err = db.Ping(); err != nil {
		panic(err)
	}

	leiermannIndexed := indexPieceFromDisk(TESTPIECE)
	queryIndexed := indexPieceFromDisk(TESTQUERY)

	/*
		vecs := VecsFromNotes(leiermannIndexed.Notes)
		println(vecs)
		for _, vec := range vecs {
			println(vec.a.PieceIdx, vec.b.PieceIdx)
		}
	*/
	println(queryIndexed.VectorsCsv)

	for _, note := range queryIndexed.Notes {
		println(note)
	}

	arrays := Search(queryIndexed, leiermannIndexed)
	fmt.Println(arrays)

	/*
		var vectors string
		println("querying")
		rows := db.QueryRowContext(context.Background(), "SELECT vectors FROM Piece;")
		rows.Scan(&vectors)
		println("vectors: %v", vectors[0:200])
		score := InitScoreFromCsv(vectors)
		print(score.num_notes)
		print(score.num_vectors)
		print(score.vectors)
	*/
}
