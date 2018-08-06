Instructions
============

get docker image for postgres image
-----------------------------------
```
https://hub.docker.com/_/postgres/
```
TODO: make docker image based on this and script to set up tables

run postgres docker container with ``web/run_postgres_docker.sh``

set up docker image with data
-----------------------------
* install psycopg2 ``pip install psycopg2``
* run docker container with ``docker run --name $NAME -e POSTGRES_PASSWORD=${PASS} -e PGDATA=/home -d -p 5432:5432 fixr_verivita_tracedb``
* create database with * create tables with ``python dbscripts/create_tables.py [password]`` TODO: command line interface for this script, currently just run with ipython


data locations
------------------------
**docker images**
100.120.0.2:5005/fixr_verivita_web_search
100.120.0.2:5005/fixr_verivita_tracedb

**psql data**
/Users/s/Documents/data/trace_query_data_psql.tgz (shawn's computer, this is generated from trace corpus on aws s3)


clone and build trace-serializer
--------------------------------
```
git clone git@github.com:cuplv/trace-serializer.git
cd trace-serializer
sbt publishLocal
```

run tracesearch with
--------------------

```
sbt run
```


notes for later
---------------
* look into materialized views to store raw trace data and generate graphs: https://docs.microsoft.com/en-us/azure/architecture/patterns/materialized-view
