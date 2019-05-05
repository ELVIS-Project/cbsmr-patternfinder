package main

import (
	pb "../proto"
	"database/sql"
	"github.com/boltdb/bolt"
	_ "github.com/lib/pq"
	log "github.com/sirupsen/logrus"
	"google.golang.org/grpc"
	vp "github.com/spf13/viper"
	"net"
	"time"
)

var server *SmrServer

type SmrServer struct{
	grpc *grpc.Server
	psqlDb *sql.DB
	boltDb *bolt.DB
	pieceMap map[uint32]CScore
}

// Global handle on a running index client
var indexerClient pb.IndexClient

func openBolt() (db *bolt.DB) {
	var err error
	db, err = bolt.Open(vp.GetString("SMR_DB"), 0666, &bolt.Options{Timeout: 1 * time.Second})
	if err != nil {
		panic(err)
	}

	db.Update(func(tx *bolt.Tx) error {
		_, err = tx.CreateBucketIfNotExists([]byte("scores"))
		if err != nil { panic(err) }
		return nil
	})

	return
}

func dialIndex() (client pb.IndexClient) {
	conn, err := grpc.Dial(vp.GetString("INDEXER_URI"), grpc.WithInsecure())

	if err != nil {
		log.Panicf("Failed to connect to indexer service, %v", err)
	}
	client = pb.NewIndexClient(conn)
	return
}

func dialPostgres() (db *sql.DB) {
	var err error
	db, err = sql.Open("postgres", vp.GetString("PSQL_STRING"))
	if err != nil {
		panic(err)
	}

	return
}

func StartServer() *SmrServer {
	// This is a global handle
	indexerClient = dialIndex()

	// These are wrapped in a SearchServer struct
	psqlDb := dialPostgres()

	boltDb := openBolt()

	println("Starting server")
	s := grpc.NewServer()
	smr := SmrServer{
		grpc: s,
		psqlDb: psqlDb,
		boltDb: boltDb,
		pieceMap: make(map[uint32]CScore),
	}
	pb.RegisterSmrServer(s, &smr)

	smr.LoadScores(WINDOW)

	ln, err := net.Listen("tcp", ":" + vp.GetString("SMR_PORT"))
	if err != nil {
		panic(err)
	}

	go func() {
		if err := s.Serve(ln); err != nil {
			panic(err)
		}
	}()

	return &smr
}

func main() {
	vp.AutomaticEnv()

	// This is a global handle
	server = StartServer()
	defer server.boltDb.Close()
	defer server.psqlDb.Close()
	defer server.grpc.GracefulStop()

	select {}

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
