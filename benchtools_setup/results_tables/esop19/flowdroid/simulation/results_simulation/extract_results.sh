#!/usr/bin/env bash
python ~/software/benchtools/analyze/extract_log.py -p -f ../../../../../filters/simulate.py -o results_${f}.txt simulation_flowdroid

for f in `ls |grep txt`
do
	BLOCK=`grep -c "result Block" $f`
	READERROR=`grep -c "result ReadError" $f`
	TIMEOUT=`grep -c "time Timeout" $f`
	UNK=`grep -c "result ? time ?" $f`
	echo "--------------------------"
	echo $f
	echo "block: $Block"
	echo "timeout: $TIMEOUT"
	echo "read error: $READERROR"
	echo "unknown: $UNK"
done
