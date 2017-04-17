for f in `ls |grep tar.bz2`
do
	python ~/software/benchtools/analyze/extract_log.py -p -f ../filters/ic3_filter.py -o results_${f}.txt $f
done

for f in `ls |grep txt`
do
	SAFE=`grep -c "Safe" $f`
	UNSAFE=`grep -c "Unsafe" $f`
	READERROR=`grep -c "ReadError" $f`
	UNK=`grep -c "result ?" $f`
	echo "--------------------------"
	echo $f
	echo "safe: $SAFE"
	echo "unsafe: $UNSAFE"
	echo "read error: $READERROR"
	echo "unknown: $UNK"
done
