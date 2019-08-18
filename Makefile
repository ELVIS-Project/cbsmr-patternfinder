.PHONY: docker proto

proto: proto/smr_pb2.py proto/smr_pb2_grpc.py proto/smr.pb.go

proto/smr_pb2.py:
	python3 -m grpc_tools.protoc -I=proto/ --python_out=proto/ proto/smr.proto

proto/smr_pb2_grpc.py:
	python3 -m grpc_tools.protoc -I=proto/ --grpc_python_out=proto/ proto/smr.proto

proto/smr.pb.go:
	protoc --go_out=./ proto/smr.proto
	protoc -I proto/ proto/smr.proto --go_out=plugins=grpc:proto --proto_path=./

docker:
	docker build . -t cbsmr:latest
