#!/bin/bash
NAME="vv_postgres"
PASS=$(cat ~/.pgpass)

docker run --name $NAME -e PGDATA="/home" -e POSTGRES_PASSWORD=${PASS} -d -p 5432:5432 "100.120.0.2:5005/fixr_verivita_tracedb"
