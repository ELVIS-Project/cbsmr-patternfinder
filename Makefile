proto:
	protoc --python_out=./ proto/types.proto
	python -m grpc_tools.protoc -I=index/ --python_out=index/ --grpc_python_out=index/ index/indexer.proto --proto_path=proto/
