Instructions
============

get docker image for postgres image
-----------------------------------
```
https://hub.docker.com/_/postgres/
```
TODO: make docker image based on this and script to set up tables


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

