VERSION_TAG?=dev-$(shell git rev-parse --short HEAD)
export VERSION_TAG

.PHONY: proto venv docker

proto:
	# Regular proto gen for python & golang
	protoc --python_out=./ --go_out=./ proto/smr.proto

	# Python grpc
	python3 -m grpc_tools.protoc -I=proto/ --python_out=proto/ --grpc_python_out=proto/ --proto_path=./ proto/smr.proto

	# Golang grpc
	protoc -I proto/ proto/smr.proto --go_out=plugins=grpc:proto --proto_path=./

venv:
	rm -rf venv
	virtualenv venv --python=python3
	source venv/bin/activate
	pip install -r requirements.txt

docker:
	docker build . -t cbsmr:latest
