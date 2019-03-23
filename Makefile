proto:
	protoc --python_out=./ proto/types.proto
	python -m grpc_tools.protoc -I=indexer/ --python_out=indexer/ --grpc_python_out=indexer/ indexer/indexer.proto --proto_path=./
