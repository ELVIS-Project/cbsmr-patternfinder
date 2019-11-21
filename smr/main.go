package main

import (
	pb "../proto"
	"github.com/boltdb/bolt"
	_ "github.com/lib/pq"
	log "github.com/sirupsen/logrus"
	"google.golang.org/grpc"
	vp "github.com/spf13/viper"
	"net"
	"fmt"
	"time"
)

func max(i, j int) int {
	if i < j {
		return j
	} else {
		return i
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

var server *SmrServer

type SmrServer struct{
	grpc *grpc.Server
	pieceStore *BoltPieceStore
	pieceMap map[PieceId]CScore
}

func openBolt() (db *bolt.DB) {
	var err error
	db, err = bolt.Open(vp.GetString("SMR_DB"), 0666, &bolt.Options{Timeout: 1 * time.Second})
	if err != nil {
		panic(fmt.Errorf("couldn't open bolt db at location %s: %s", vp.GetString("SMR_DB"), err))
	} else {
		log.Infof("connected to bolt %v", vp.GetString("SMR_DB"))
	}

	return
}

func StartServer() *SmrServer {

	boltDb := openBolt()
	pieceStore, err := NewBoltPieceStore(boltDb)
	if err != nil {
		panic(err)
	}

	println("Starting server")
	s := grpc.NewServer()
	smr := SmrServer{
		grpc: s,
		pieceStore: pieceStore,
		pieceMap: make(map[PieceId]CScore),
	}
	pb.RegisterSmrServer(s, &smr)

	/*
	err := smr.LoadScores(WINDOW)
	if err != nil {
		panic(err)
	}
	*/

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
	defer server.pieceStore.Close()
	defer server.grpc.GracefulStop()

	select {}

}
