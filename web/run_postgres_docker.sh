#!/bin/bash
NAME="vv_postgres"
PASS=$(cat ~/.pgpass)

docker run --name $NAME -e POSTGRES_PASSWORD=${PASS} -d -p 5432:5432 postgres
