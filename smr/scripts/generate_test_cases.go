package main

import (
	pb "../../proto"
	smr ".."
	"path"
	"io/ioutil"
)

const (
	TESTDATA = "../testdata"
	LEMSTROM = path.Join(TESTDATA, "lemstrom2011")
	LEIERMANN = path.Join(LEMSTROM, "leiermann.xml")
	QUERY_A = path.Join(LEMSTROM, "query_a.mid")
	QUERY_B = path.Join(LEMSTROM, "query_b.mid")
	QUERY_C = path.Join(LEMSTROM, "query_c.mid")
	QUERY_D = path.Join(LEMSTROM, "query_d.mid")
)

func main() {
	for queryPath := range []string{QUERY_A, QUERY_B, QUERY_C, QUERY_D} {
		pbNotes := smr.PbNotesFromNotes(
