proto:
	protoc --python_out=./ --go_out=./ proto/types.proto
	python -m grpc_tools.protoc -I=proto/ --python_out=proto/ --grpc_python_out=proto/ --proto_path=./ proto/indexer.proto
	protoc -I proto/ proto/indexer.proto --go_out=plugins=grpc:proto --proto_path=./
	protoc -I proto/ proto/search.proto --go_out=plugins=grpc:proto --proto_path=./

venv:
	rm -rf venv
	virtualenv venv --python=python3
	source venv/bin/activate
	pip install -r requirements.txt
