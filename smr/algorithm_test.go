package main

import (
	//"fmt"
	"testing"
	pb "../proto"
	"io/ioutil"
	"github.com/golang/protobuf/proto"
)

var (
	QuarterNotesCD = []Note {
		{Onset: 0, Duration: 0, Pitch: 162},
		{Onset: 1, Duration: 0, Pitch: 168},
	}
	QuarterNotesDE = []Note {
		{Onset: 0, Duration: 0, Pitch: 168},
		{Onset: 1, Duration: 0, Pitch: 174},
	}
	QuarterNotesGAB = []Note {
		{Onset: 0, Duration: 0, Pitch: 185},
		{Onset: 1, Duration: 0, Pitch: 191},
		{Onset: 2, Duration: 0, Pitch: 197},
	}
)

func UnmarshalIdxRespFromFile(path string) *pb.IndexResponse {
	fileBytes, err := ioutil.ReadFile(path)
	xk(err)
	idxResp := &pb.IndexResponse{}
	xk(proto.Unmarshal(fileBytes, idxResp))
	return idxResp
}

func NotesFromFile(path string) []Note {
	idxResp := UnmarshalIdxRespFromFile(path)
	return NotesFromPbNotes(idxResp.Notes)
}

func TestTranspositions(t *testing.T) {
	var windowSize = 2

	testCases := []struct {
		window int
		query []Note
		target []Note
		expected Results
	}{
		{
			2,
			QuarterNotesCD,
			QuarterNotesDE,
			Results{QuarterNotesDE},
		},
		{
			2,
			QuarterNotesCD,
			[]Note{
				{Onset: 0, Duration: 0, Pitch: 185},
				{Onset: 1, Duration: 0, Pitch: 191},
				{Onset: 2, Duration: 0, Pitch: 197},
			},
			Results{
				[]Note{
					{Onset: 0, Duration: 0, Pitch: 185},
					{Onset: 1, Duration: 0, Pitch: 191},
				},
				[]Note {
					{Onset: 1, Duration: 0, Pitch: 191},
					{Onset: 2, Duration: 0, Pitch: 197},
				},
			},
		},
		{
			3,
			QuarterNotesCD,
			[]Note{
				{Onset: 0, Duration: 0, Pitch: 185},
				{Onset: 1, Duration: 0, Pitch: 191},
				{Onset: 2, Duration: 0, Pitch: 197},
			},
			Results{
				[]Note{
					{Onset: 0, Duration: 0, Pitch: 185},
					{Onset: 1, Duration: 0, Pitch: 191},
				},
				[]Note {
					{Onset: 1, Duration: 0, Pitch: 191},
					{Onset: 2, Duration: 0, Pitch: 197},
				},
			},
		},
		{
			6,
			QuarterNotesCD,
			[]Note{
				{Onset: 0, Duration: 0, Pitch: 185},
				{Onset: 0.5, Duration: 0, Pitch: 300},
				{Onset: 1, Duration: 0, Pitch: 191},
				{Onset: 1.5, Duration: 0, Pitch: 300},
				{Onset: 1.7, Duration: 0, Pitch: 300},
				{Onset: 2, Duration: 0, Pitch: 197},
			},
			Results{
				[]Note{
					{Onset: 0, Duration: 0, Pitch: 185},
					{Onset: 1, Duration: 0, Pitch: 191},
				},
				[]Note {
					{Onset: 1, Duration: 0, Pitch: 191},
					{Onset: 2, Duration: 0, Pitch: 197},
				},
			},
		},
		{
			4,
			// :todo
			// Tests duplicates
			// Tests partial matches...
			QuarterNotesGAB,
			[]Note{
				{Onset: 0, Duration: 0, Pitch: 300},
				{Onset: 0.5, Duration: 0, Pitch: 300},
				{Onset: 3.5, Duration: 0, Pitch: 300},
				{Onset: 4, Duration: 0, Pitch: 185},
				{Onset: 5, Duration: 0, Pitch: 191},
				{Onset: 6, Duration: 0, Pitch: 197},
				{Onset: 6.5, Duration: 0, Pitch: 300},
				{Onset: 7, Duration: 0, Pitch: 225},
				{Onset: 8, Duration: 0, Pitch: 231},
				{Onset: 9, Duration: 0, Pitch: 237},
				{Onset: 9.5, Duration: 0, Pitch: 300},
			},
			Results{
				[]Note{
					{Onset: 4, Duration: 0, Pitch: 185},
					{Onset: 5, Duration: 0, Pitch: 191},
					{Onset: 6, Duration: 0, Pitch: 197},
				},
				[]Note {
					{Onset: 7, Duration: 0, Pitch: 225},
					{Onset: 8, Duration: 0, Pitch: 231},
					{Onset: 9, Duration: 0, Pitch: 203},
				},
			},
		},
	}

	for _, test := range testCases {
		for _, transpose := range []int{0, 5, 7} {
			target := make([]Note, len(test.target))
			for i := range test.target {
				target[i] = test.target[i]
				target[i].Pitch = target[i].Pitch + (Base40Type)(transpose)
			}
			expected := make(Results, len(test.expected))
			for i := range test.expected {
				expected[i] = make([]Note, len(test.expected[i]))
				for j := range test.expected[i] {
					expected[i][j] = test.expected[i][j]
					expected[i][j].Pitch = expected[i][j].Pitch + (Base40Type)(transpose)
				}
			}

			//fmt.Printf("Testing query %v against target %v with window %v\n", test.query, target, test.window)

			windowSize = test.window
			binsInit()
			PreProcess(target, windowSize)

			//println("\nBINS")
			//printBins()

			/*
			res := Query(test.query, windowSize)

			fmt.Printf("expected %v, found %v\n", expected, res)

			if len(expected) != len(res) {
				t.Errorf("missing results, expected %v, got %v", expected, res)
			}
			for i := range expected {
				// skip partial matches
				if len(res[i]) != len(test.query) { continue }

				if len(expected[i]) != len(res[i]) {
					t.Errorf("length differs, expected %v, got %v", expected[i], res[i])
				}
				for j := range expected[i] {
					if expected[i][j] != res[i][j] {
						t.Errorf("notes differ, expected %v, got %v", expected[i], res[i])
					}
				}
			}
			*/
		}
	}
}

func TestAlgorithmLemstrom(t *testing.T) {
	testCases := []struct {
		window int
		query []Note
		target []Note
		expected Results
	}{
		{
			11,
			NotesFromFile(LEIERMANN_QUERY[0] + ".idxresp_notes"),
			NotesFromFile(LEIERMANN + ".idxresp_notes"),
			Results{},
		},
		/*
		{
			9,
			NotesFromFile(LEIERMANN_QUERY[1] + ".idxresp_notes"),
			NotesFromFile(LEIERMANN + ".idxresp_notes"),
			Results{},
		},
		*/
		/* Scaled occurrence
		{
			9,
			NotesFromFile(LEIERMANN_QUERY[2] + ".pb_notes"),
			NotesFromFile(LEIERMANN + ".pb_notes"),
			Results{},
		},
		*/
	}

	for _, test := range testCases {
		//log.Debugf("QUERY: %v\n", test.query)
		//log.Debugf("TARGET: %v\n", test.target)

		PreProcess(test.target, test.window)

		//println("\nbins")
		//printBins()

		/*
		res := Query(test.query, test.window)

		for _, notes := range res {
			if len(notes) < 6 { continue }
			//log.Debugf(fmt.Sprintf("Result: %v\n", notes))
			//log.Debugf(fmt.Sprintf("Indices: %v\n", res.asNoteIndices(test.target))
		}
		*/
	}
}

/*
func TestAlgorithmSimpleCases(t *testing.T) {
	windowSize = 2

	testCases := []struct {
		window int
		query []Note
		target []Note
		result string
	}{
		{
			// Two occurrences, unscaled
			2,
			[]Note {
				{Onset: 0, Duration: 1, Pitch: 10},
				{Onset: 2, Duration: 1, Pitch: 20},
			},
			[]Note {
				{Onset: 0, Duration: 1, Pitch: 10},
				{Onset: 2, Duration: 1, Pitch: 20},
				{Onset: 4, Duration: 1, Pitch: 30},
			},
			"[[{0 1 10} {2 1 20}] [{2 1 20} {4 1 30}]]",
		},
		{
			// One occurrence, scaled
			2,
			[]Note {
				{Onset: 0, Duration: 1, Pitch: 10},
				{Onset: 2, Duration: 1, Pitch: 20},
			},
			[]Note {
				{Onset: 0, Duration: 2, Pitch: 10},
				{Onset: 4, Duration: 2, Pitch: 20},
			},
			"[[{0 2 10} {4 2 20}]]",
		},
		{
			// Two occurrences, one is scaled
			2,
			[]Note {
				{Onset: 0, Duration: 1, Pitch: 10},
				{Onset: 2, Duration: 1, Pitch: 20},
			},
			[]Note {
				{Onset: 0, Duration: 2, Pitch: 10},
				{Onset: 4, Duration: 2, Pitch: 20},
				{Onset: 8, Duration: 1, Pitch: 10},
				{Onset: 10, Duration: 1, Pitch: 20},
			},
			"[[{0 2 10} {4 2 20}] [{8 1 10} {10 1 20}]]",
		},
		{
			// Two occurrences, one is scaled, embedded within larger score
			3,
			[]Note {
				{Onset: 0, Duration: 1, Pitch: 10},
				{Onset: 2, Duration: 1, Pitch: 20},
				{Onset: 4, Duration: 1, Pitch: 50},
			},
			[]Note {
				{Onset: 0, Duration: 0, Pitch: 20},
				{Onset: 1, Duration: 0, Pitch: 20},
				{Onset: 2, Duration: 0, Pitch: 20},
				{Onset: 3, Duration: 0, Pitch: 20},
				{Onset: 4, Duration: 1, Pitch: 20},
				{Onset: 6, Duration: 1, Pitch: 30},
				{Onset: 8, Duration: 1, Pitch: 60},
				{Onset: 10, Duration: 0, Pitch: 40},
				{Onset: 11, Duration: 0, Pitch: 40},
				{Onset: 12, Duration: 2, Pitch: 20},
				{Onset: 16, Duration: 2, Pitch: 30},
				{Onset: 20, Duration: 2, Pitch: 60},
			},
			"[[{4 1 20} {6 1 30} {8 6 40}] [{12 2 20} {16 2 30} {20 2 40}]]",
		},
	}

	for _, test := range testCases {
		fmt.Printf("Testing query %v against target %v with window %v\n", test.query, test.target, test.window)

		windowSize = test.window

		binsInit()

		PreProcess(test.target)

		res := fmt.Sprintf("%v", Query(test.query))

		//println("\nBINS")
		//printBins()

		if res != test.result {
			t.Errorf("failed, expected %v, got %v", test.result, res)
		}
	}
}

func TestAlgorithmLemstrom(t *testing.T) {
	windowSize=9

	query := NotesFromFile(LEIERMANN_QUERY[0] + ".pb_notes")
	target := NotesFromFile(LEIERMANN + ".pb_notes")

	println("\n QUERY")
	for i := range query {
		fmt.Printf("%v: %v\n", i, query)
	}
	println("\n TARGET")
	for i := range target {
		fmt.Printf("%v: %v\n", i, target)
	}

	PreProcess(target)

	res := Query(query)
	//resNotes := res.ToNoteIndices(targetResp.Notes)

	for _, notes := range res {
		if len(notes) < 4 { continue }
		//fmt.Printf("%v\n", notes)
		//fmt.Printf("%v\n", resNotes[i])
	}
}

func TestNormalize(t *testing.T) {
	target := []Note{
		{Onset: 0, Duration: 1, Pitch: 10},
		{Onset: 2, Duration: 1, Pitch: 20},
		{Onset: 4, Duration: 1, Pitch: 30},
	}
	window := Window(target)
	nw := window.Normalize(Basis{target[0], target[1]})
	if fmt.Sprintf("%v", nw) != "[{0 0 0} {1 0 10} {2 0 20}]" {
		t.Fail()
	}
}

func TestDenormalize(t *testing.T) {
	target := []Note{
		{Onset: 0, Duration: 1, Pitch: 10},
		{Onset: 2, Duration: 1, Pitch: 20},
		{Onset: 4, Duration: 1, Pitch: 30},
	}
	basis := Basis{target[0], target[1]}
	window := Window(target)
	nw := window.Normalize(basis)
	dw := nw.Denormalize(basis)

	// Round trip
	if len(nw) != len(dw) { t.Fail() }
	for i, _ := range nw {
		if window[i] != dw[i] {
			t.Fail()
		}
	}
}
*/
