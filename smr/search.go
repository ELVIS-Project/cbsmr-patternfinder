package main

import (
	"context"
	pb "../proto"
	"fmt"
)

func (s SmrServer) Search(ctx context.Context, req *pb.Notes) (occs *pb.Occurrences, err error) {

	vecs := VecsFromNotes(req)
	queryScore := InitScoreFromVectors(len(req.Notes), vecs)

	for pieceID, cscore := range s.pieceMap {
		intArrays := search(queryScore, cscore)
		println(fmt.Sprintf("%v", intArrays))
		for _, arr := range intArrays {
			(*occs).Occurrences = append((*occs).Occurrences, &pb.Occurrence{Pid: pieceID, Notes: arr})
		}
	}

	return occs, nil
}
