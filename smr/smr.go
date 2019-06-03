package main

import (
	pb "../proto"
	"context"
	log "github.com/sirupsen/logrus"
)

func (s *SmrServer) GetPieceIds(ctx context.Context, req *pb.GetPieceIdsRequest) (resp *pb.GetPieceIdsResponse, err error) {
	pids, err := s.pieceStore.ListIds()

	var pbIds []uint32
	for _, pid := range pids {
		pbIds = append(pbIds, pid.toPbPieceId())
	}
	return &pb.GetPieceIdsResponse{Pids: pbIds}, err
}

func (s *SmrServer) AddPiece(ctx context.Context, req *pb.AddPieceRequest) (resp *pb.AddPieceResponse, err error) {
	notes := NotesFromPbNotes(req.Notes)
	vecs := VecsFromNotes(notes)
	pid := PieceId(req.Pid)

	piece := Piece {
		Notes: notes,
		Vectors: vecs,
		Pid: pid,
	}

	err = s.pieceStore.Set(pid, piece)

	//err = s.LoadOneScore(pid, WINDOW)

	log.Infoln("Put in a score! id: ", pid)
	return &pb.AddPieceResponse{}, err
}

func (s SmrServer) Search(ctx context.Context, req *pb.SearchRequest) (resp *pb.SearchResponse, err error) {

	notes := NotesFromPbNotes(req.Notes)
	//occs, err = Search(s.pieceMap, notes)
	occs, err := s.pieceStore.Search(notes)
	if err != nil {
		return &pb.SearchResponse{}, err
	}

	var pbOccs []*pb.Occurrence
	for _, occ := range occs {
		pbOccs = append(pbOccs, occ.toPbOcc())
	}
	return &pb.SearchResponse{Occurrences: pbOccs} , nil
}
