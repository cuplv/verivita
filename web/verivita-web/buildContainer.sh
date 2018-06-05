cp -r ../../cbverifier .
cp ../../nuXmv-1.1.1-linux64.tar.gz .
sbt dist
unzip target/universal/play-elm-example-1.0-SNAPSHOT.zip
docker build -t vvweb .
rm -r cbverifier
rm -r nuXmv-1.1.1-linux64.tar.gz
rm -r play-elm-example-1.0-SNAPSHOT

