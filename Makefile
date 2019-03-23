proto:
	protoc --python_out=./ proto/types.proto
	python -m grpc_tools.protoc -I=indexer/ --python_out=indexer/ --grpc_python_out=indexer/ indexer/indexer.proto --proto_path=./

venv:
	rm -rf venv
	virtualenv venv --python=python3
	source venv/bin/activate
	pip install -r requirements.txt
