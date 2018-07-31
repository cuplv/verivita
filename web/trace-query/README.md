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
* create database with TODO
* create tables with ``python dbscripts/create_tables.py [password]``



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

