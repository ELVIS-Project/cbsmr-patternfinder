package main

import (
	"io/ioutil"
	"github.com/golang/protobuf/proto"
	pb "../proto"
)

var (
	LEIERMANN = "./testdata/lemstrom2011/leiermann"
	LEIERMANN_QUERY = []string{
		"./testdata/lemstrom2011/query_a",
		"./testdata/lemstrom2011/query_b",
		"./testdata/lemstrom2011/query_c",
		"./testdata/lemstrom2011/query_d",
		"./testdata/lemstrom2011/query_e",
		"./testdata/lemstrom2011/query_f",
	}
	PALESTRINA = "./testdata/palestrina_masses/"
	TESTPIECES = []string{
		"./testdata/000000000002557_Regina-caeli-letare_Josquin-Des-Prez_file5.mei",
		"./testdata/000000000002678_Sancta-mater-istud-agas_Penalosa-Francisco_file5.mei",
		"./testdata/000000000010113_Sonata-in-G-minor-Op.-4-No.-2_Grave_Corelli-Arcangelo_file1.xml",
		"./testdata/000000000010138_Je-me-recommande_Binchois-Gilles-de-Bins-dit_file1.xml",
	}
)

func InitScoreFromFile(path string) (CScore) {
	notes := UnmarshalNotesFromFile(path)
	vecs := VecsFromNotes(notes)
	return InitScoreFromVectors(len(notes.Notes), vecs)
}

func UnmarshalNotesFromFile(path string) (*pb.Notes){
	fileBytes, err := ioutil.ReadFile(path)
	xk(err)
	pbNotes := &pb.Notes{}
	xk(proto.Unmarshal(fileBytes, pbNotes))
	return pbNotes
}


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
