#!/usr/bin/bash

docker-compose up db -f ../db

pg_isready --host localhost
while [ $? -ne 0 ]; do sleep 1; pg_isready --host localhost; done

python3 client.py $1

docker-compose down db
