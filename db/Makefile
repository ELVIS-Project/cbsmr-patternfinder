db: dockerclean dockerbuild rmdb
	docker-compose up db

rmdb:
	rm -rf postgres-data

dockerbuild:
	docker build . -t scmr_db:latest

make dockerclean:
	docker-compose down
