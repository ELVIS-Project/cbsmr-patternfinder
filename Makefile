proto:
	protoc --python_out=./ --go_out=./ proto/types.proto
	python -m grpc_tools.protoc -I=indexer/ --python_out=indexer/ --grpc_python_out=indexer/ --proto_path=./ indexer/indexer.proto
	protoc -I indexer/ indexer/indexer.proto --go_out=plugins=grpc:proto --proto_path=./

venv:
	rm -rf venv
	virtualenv venv --python=python3
	source venv/bin/activate
	pip install -r requirements.txt
