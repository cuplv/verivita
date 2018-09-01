#!/bin/bash
cp ../target/universal/vvweb-1.0-SNAPSHOT.zip .
unzip vvweb-1.0-SNAPSHOT.zip
docker build -t vvweb .
rm -r vvweb-1.0-SNAPSHOT*

