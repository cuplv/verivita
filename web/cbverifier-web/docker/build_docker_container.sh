mkdir verivita
mkdir verivita/software
mkdir verivita/app
cp -r ~/Documents/source/verivita/cbverifier verivita/cbverifier
tar -xf ~/Documents/source/verivita/nuXmv-1.1.1-linux64.tar.gz --directory verivita/software/
cp ~/Documents/source/verivita/web/cbverifier-web/*.py verivita/app/
cp -r pysmt ~/

docker build -t fixr_cbverifier .

rm -r verivita

