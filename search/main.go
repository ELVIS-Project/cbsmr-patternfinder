package main

import (
	pb "../proto"
	"context"
	"database/sql"
	"github.com/boltdb/bolt"
	_ "github.com/lib/pq"
	log "github.com/sirupsen/logrus"
	"google.golang.org/grpc"
	"net"
	"time"
)

const (
	DBSTRING = "host=localhost port=5432 user=postgres password=postgres sslmode=disable"
)

var indexerClient pb.IndexerClient
var psqlDb *sql.DB
var boltDb *bolt.DB
var pieceMap map[uint32]CScore = make(map[uint32]CScore)

type SearchServer struct{}

func (s SearchServer) Search(ctx context.Context, req *pb.SearchRequest) (resp *pb.SearchResponse, err error) {

	var occs []*pb.Occurrence

	println("index query")
	queryIndexResp, err := indexerClient.IndexPiece(context.Background(), &pb.IndexRequest{Piece: &pb.Piece{SymbolicData: req.SymbolicData}})
	if err != nil {
		log.Infoln("Failed to index query in request")
		return nil, err
	}
	println("init score query")
	queryScore := InitScoreFromCsv(queryIndexResp.VectorsCsv)

	for pieceID, cscore := range pieceMap {
		intArrays := search(queryScore, cscore)
		for _, arr := range intArrays {
			occs = append(occs, &pb.Occurrence{PieceId: pieceID, NoteIdx: arr})
		}
	}

	resp = &pb.SearchResponse{Occs: occs}

	return resp, nil
}

func openBolt() (db *bolt.DB) {
	db, err := bolt.Open("smr.db", 0600, &bolt.Options{Timeout: 1 * time.Second})
	if err != nil {
		panic("Failed to open bolt database")
	}
	return
}

func dialIndexer() (client pb.IndexerClient) {
	conn, err := grpc.Dial("localhost:50051", grpc.WithInsecure())
	if err != nil {
		log.Panicf("Failed to connect to indexer service, %v", err)
	}
	client = pb.NewIndexerClient(conn)
	return
}

func dialPostgres() (db *sql.DB) {
	var err error
	db, err = sql.Open("postgres", DBSTRING)
	if err != nil {
		panic(err)
	}

	if err = db.Ping(); err != nil {
		panic(err)
	}

	return
}

func loadScores() {

	var (
		id      uint32
		vectors string
	)

	rows, err := psqlDb.QueryContext(context.Background(), "SELECT id, vectors FROM Piece;")
	if err != nil {
		panic(err)
	}

	for rows.Next() {
		err = rows.Scan(&id, &vectors)
		if err != nil {
			panic("Failed to scan psql result")
		}

		score := InitScoreFromCsv(vectors)
		pieceMap[id] = score
	}

	/*
		boltDb.Update(
			func (tx *bolt.Tx) {
				piecesBucket := tx.CreateBucketIfNotExists("pieces")
				piecesBucket.Put()
			}
		)
	*/
}

func StartServer() *grpc.Server {

	println("Dialing indexer")
	indexerClient = dialIndexer()

	println("Dialing postgres")
	psqlDb = dialPostgres()
	defer psqlDb.Close()

	println("Opening Bolt")
	boltDb = openBolt()
	defer boltDb.Close()

	println("Loading scores into memory")
	loadScores()

	println("Starting server")
	s := grpc.NewServer()
	pb.RegisterSearcherServer(s, &SearchServer{})

	ln, err := net.Listen("tcp", ":8080")
	if err != nil {
		panic("Failed to listen on TCP")
	}

	go func() {
		if err := s.Serve(ln); err != nil {
			panic("Failed to serve!")
		}
	}()

	return s
}

func main() {

	server := StartServer()

	select {}

	server.GracefulStop()

	/*

		/*
			vecs := VecsFromNotes(leiermannIndexed.Notes)
			println(vecs)
			for _, vec := range vecs {
				println(vec.a.PieceIdx, vec.b.PieceIdx)
			}
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
