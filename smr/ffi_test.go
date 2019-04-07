package main

import (
	pb "../proto"
	"context"
	"fmt"
	log "github.com/sirupsen/logrus"
	"google.golang.org/grpc"
	"io/ioutil"
	"testing"
)

var (
	TESTPIECES = []string{
		"./testdata/000000000002557_Regina-caeli-letare_Josquin-Des-Prez_file5.mei",
		"./testdata/000000000002678_Sancta-mater-istud-agas_Penalosa-Francisco_file5.mei",
		"./testdata/000000000010113_Sonata-in-G-minor-Op.-4-No.-2_Grave_Corelli-Arcangelo_file1.xml",
		"./testdata/000000000010138_Je-me-recommande_Binchois-Gilles-de-Bins-dit_file1.xml",
	}
	TESTPALESTRINA = []string{
		"./testdata/palestrina_masses/000000000011125_Missa-Hodie-christus-natus-est_Sanctus_Palestrina-Giovanni-Pierluigi-da_file2.mid",
		"./testdata/palestrina_masses/000000000011344_Missa-Primi-toni_Credo_Palestrina-Giovanni-Pierluigi-da_file2.mid",
	}
)

func indexPieceFromDisk(path string) *pb.IndexResponse {

	println("Dialing indexer")
	conn, err := grpc.Dial("localhost:50051", grpc.WithInsecure())
	if err != nil {
		log.Panicf("Failed to connect to indexer service, %v", err)
	}
	indexerClient = pb.NewIndexerClient(conn)

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

/*
func TestLemstrom(t *testing.T) {

	leiermannIndexed := indexPieceFromDisk(TESTPIECE)
	queryIndexed := indexPieceFromDisk(TESTQUERY)

	query := InitScoreFromCsv(queryIndexed.VectorsCsv)
	leiermann := InitScoreFromCsv(leiermannIndexed.VectorsCsv)

	arrays := search(query, leiermann)

	println(fmt.Sprintf("%v", arrays))

	if fmt.Sprintf("%v", arrays) != "[[3 6 8 9 16 21] [13 14 16 17 18 21]]" {
		t.Fail()
	}
}
*/

func TestLemstrom(t *testing.T) {
	queryIndexed := indexPieceFromDisk(TESTQUERY)
	pieceIndexed := indexPieceFromDisk(TESTPIECE)

	vecs := VecsFromNotes(queryIndexed.Notes)
	Tvecs := VecsFromNotes(pieceIndexed.Notes)

	pattern := InitScoreFromVectors(len(queryIndexed.Notes), vecs)
	target := InitScoreFromVectors(len(pieceIndexed.Notes), Tvecs)

	//PrintScore(s)
	//PrintScore(Ts)

	results := search(pattern, target)

	println(fmt.Sprintf("%v", results))
}

func TestPalestrina(t *testing.T) {
	for _, path := range TESTPALESTRINA {
		targetIndexed := indexPieceFromDisk(path)

		pbNotes := []*pb.Note{
			&pb.Note{Onset: 0, Offset: 1, PitchB40: 163, PieceIdx: 0},
			&pb.Note{Onset: 1, Offset: 2, PitchB40: 180, PieceIdx: 1},
			&pb.Note{Onset: 2, Offset: 3, PitchB40: 163, PieceIdx: 2},
		}
		pVecs := VecsFromNotes(pbNotes)
		tVecs := VecsFromNotes(targetIndexed.Notes[:100])

		println(fmt.Sprintf("%v", pVecs))

		println("pattern score")
		pattern := InitScoreFromVectors(len(pbNotes), pVecs)
		println("target score")
		target := InitScoreFromVectors(len(targetIndexed.Notes), tVecs)

		println("search")
		results := search(pattern, target)

		println(fmt.Sprintf("%v", results))
	}
}
