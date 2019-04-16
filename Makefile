SMR_VERSION?=dev-$(shell git rev-parse --short HEAD)
export SMR_VERSION

INDEXER_PORT?=8080
SMR_PORT?=8081
FLASK_PORT?=8082

.PHONY: proto venv db rmdb down dsmr dflask dindexer indexer


#REGISTRY?=registry
#DOCKERFILES=$(shell find * -type f -name Dockerfile)
#IMAGES=$(subst /,\:,$(subst /Dockerfile,,$(DOCKERFILES)))
#$(IMAGES): %:
#    docker build -t $(REGISTRY)/$@ $(subst :,/,$@)

proto:
	# Regular proto gen for python & golang
	protoc --python_out=./ --go_out=./ proto/smr.proto

	# Python grpc
	python -m grpc_tools.protoc -I=proto/ --python_out=proto/ --grpc_python_out=proto/ --proto_path=./ proto/smr.proto

	# Golang grpc
	protoc -I proto/ proto/smr.proto --go_out=plugins=grpc:proto --proto_path=./

venv:
	rm -rf venv
	virtualenv venv --python=python3
	source venv/bin/activate
	pip install -r requirements.txt

db: down rmdb
	docker-compose up db

rmdb:
	rm -rf db/postgres-data

down:
	docker-compose down

docker:
	docker build . -t cbsmr:latest

dsmr:
	docker build . -f smr/Dockerfile -t smr:${SMR_VERSION}
dindexer:
	docker build . -f indexer/Dockerfile -t indexer:${SMR_VERSION}
dflask:
	docker build . -f flask/Dockerfile -t flask:${SMR_VERSION}

indexer:
	docker-compose build indexer
	docker-compose up indexer
