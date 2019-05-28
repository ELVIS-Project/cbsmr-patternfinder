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
	boltDb *bolt.DB
	pieceMap map[uint32]CScore
}

func openBolt() (db *bolt.DB) {
	var err error
	db, err = bolt.Open(vp.GetString("SMR_DB"), 0666, &bolt.Options{Timeout: 1 * time.Second})
	if err != nil {
		panic(err)
	} else {
		log.Infof("connected to bolt %v", vp.GetString("SMR_DB"))
	}


	db.Update(func(tx *bolt.Tx) error {
		_, err = tx.CreateBucketIfNotExists([]byte("scores"))
		if err != nil { panic(err) }
		return nil
	})

	return
}

func StartServer() *SmrServer {

	boltDb := openBolt()

	println("Starting server")
	s := grpc.NewServer()
	smr := SmrServer{
		grpc: s,
		boltDb: boltDb,
		pieceMap: make(map[uint32]CScore),
	}
	pb.RegisterSmrServer(s, &smr)

	err := smr.LoadScores(WINDOW)
	if err != nil {
		panic(err)
	}

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
	defer server.grpc.GracefulStop()

	select {}

}
