#!/usr/bin/env bash
for f in `ls |grep tar.bz2`
do
	python ~/software/benchtools/analyze/extract_log.py -p -f /Users/s/Documents/source/verivita/benchtools_setup/filters/ic3_filter.py -o results_${f}.txt $f
done

for f in `ls |grep txt`
do
	SAFE=`grep -c "result Safe" $f`
	UNSAFE=`grep -c "result Unsafe" $f`
	READERROR=`grep -c "result ReadError" $f`
	TIMEOUT=`grep -c "time Timeout" $f`
	UNK=`grep -c "result ? time ?" $f`
	echo "--------------------------"
	echo $f
	echo "safe: $SAFE"
	echo "unsafe: $UNSAFE"
	echo "timeout: $TIMEOUT"
	echo "read error: $READERROR"
	echo "unknown: $UNK"
done
