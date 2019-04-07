package main

import (
	"context"
	pb "../proto"
	"fmt"
)

func (s SmrServer) Search(ctx context.Context, req *pb.Notes) (occs *pb.Occurrences, err error) {
	print("Handling search!")
	occs = &pb.Occurrences{}

	vecs := VecsFromNotes(req)
	queryScore := InitScoreFromVectors(len(req.Notes), vecs)

	for pieceID, cscore := range s.pieceMap {
		print("searching ", pieceID)
		intArrays := search(queryScore, cscore)
		println(fmt.Sprintf("%v", intArrays))
		for i, arr := range intArrays {
			print("occ ", i)
			occs.Occurrences = append(occs.Occurrences, &pb.Occurrence{Pid: pieceID, Notes: arr})
		}
	}

	if len(occs.Occurrences) == 0 {
		return &pb.Occurrences{}, nil
	}

	return occs, nil
}
