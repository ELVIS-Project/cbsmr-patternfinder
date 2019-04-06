package main

import (
	pb "../../proto"
	"context"
	"testing"
	"io/ioutil"
	"google.golang.org/grpc"
	"github.com/golang/protobuf/proto"
)

const (
	leiermann_path = "./leiermann"
)

func xk(err error) {
	if err != nil {
		panic(err)
	}
}

func TestIndexNotes(t *testing.T) {
	conn, err := grpc.Dial("localhost:50051", grpc.WithInsecure())
	xk(err)
	indexerClient := pb.NewIndexClient(conn)

	sd, err := ioutil.ReadFile(leiermann_path + ".xml")
	xk(err)

	expectedBytes, err := ioutil.ReadFile(leiermann_path + ".pb_notes")
	xk(err)

	expectedNotes := &pb.Notes{}
	xk(proto.Unmarshal(expectedBytes, expectedNotes))

	queryIndexResp, err := indexerClient.IndexNotes(context.Background(), &pb.IndexRequest{SymbolicData: sd})
	xk(err)

	if expectedNotes != queryIndexResp {
		t.Errorf("\ngot\n%v\nexpected\n%v", queryIndexResp.Notes, expectedNotes)
	}
}
