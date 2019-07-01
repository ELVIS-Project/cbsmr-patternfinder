package main

import (
	"io/ioutil"
	"github.com/boltdb/bolt"
	"time"
	"os"
	"testing"
	"path"
	log "github.com/sirupsen/logrus"
	"github.com/golang/protobuf/proto"
	pb "../proto"
)

var BOLT *bolt.DB

var (
	TESTDATA = "./testdata"
	PALESTRINA = path.Join(TESTDATA, "palestrina_masses")
	LEMSTROM = path.Join(TESTDATA, "lemstrom2011")
	LEIERMANN = path.Join(LEMSTROM, "leiermann")
	QUERIES = path.Join(TESTDATA, "queries")
	LEIERMANN_QUERY = []string{
		path.Join(LEMSTROM, "query_a"),
		path.Join(LEMSTROM, "query_b"),
		path.Join(LEMSTROM, "query_c"),
		path.Join(LEMSTROM, "query_d"),
		path.Join(LEMSTROM, "query_e"),
		path.Join(LEMSTROM, "query_f"),
	}
)

func rpanic(path string) []byte {
	data, err := ioutil.ReadFile(path)
	if err != nil {
		panic(err)
	}
	return data
}

func xk(err error) {
	if err != nil {
		panic(err)
	}
}

func testOpenBolt() (db *bolt.DB) {
	var err error
	db, err = bolt.Open("smr_test.db", 0666, &bolt.Options{Timeout: 3 * time.Second})
	if err != nil {
		panic(err)
	}

	return
}

func closeBolt() {
	os.Remove("smr_test.db")
}

func TestMain(t *testing.T) {
	log.SetLevel(log.DebugLevel)
	log.SetOutput(os.Stdout)
}

func InitScoreFromFile(path string, window int) (CScore) {
	notes := UnmarshalNotesFromFile(path)
	vecs := VecsFromNotes(notes, window)
	return InitScoreFromVectors(len(notes), vecs)
}

func UnmarshalNotesFromFile(path string) ([]Note){
	fileBytes, err := ioutil.ReadFile(path)
	xk(err)
	idxResp := &pb.IndexResponse{}
	xk(proto.Unmarshal(fileBytes, idxResp))
	notes := NotesFromPbNotes(idxResp.Notes)
	return notes
}

func NewPieceFromFile(path string, id PieceId, window int) Piece {
	notes := UnmarshalNotesFromFile(path)
	vecs := VecsFromNotes(notes, window)
	return Piece {
		Notes: notes,
		Vectors: vecs,
		Pid: id,
	}
}


/*
func TestPalestrina(t *testing.T) {
	server := StartServer()

	target := InitScoreFromCsv(indexPieceFromDisk(TESTPIECE).VectorsCsv)

	pieceMap = map[uint32]CScore{0: target}

	conn, err := grpc.Dial("localhost:8080", grpc.WithInsecure())
	if err != nil {
		t.Errorf("Failed to dial searcher microservice")
	}
	searchClient := pb.NewSearcherClient(conn)

	println("Search request to server...")
	resp, err := searchClient.Search(context.Background(), &pb.SearchRequest{SymbolicData: query})
	if err != nil {
		panic(err)
	}

	if fmt.Sprintf("%v", resp.Occs[0].NoteIdx) != "[3 6 8 9 16 21]" {
		t.Fail()
	}
	if fmt.Sprintf("%v", resp.Occs[1].NoteIdx) != "[13 14 16 17 18 21]" {
		t.Fail()
	}
	server.GracefulStop()
}
*/
