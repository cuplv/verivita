#!/usr/bin/env bash

python ~/software/benchtools/analyze/extract_log.py -p -f ~/Documents/source/callback-verification/benchtools_setup/filters/simulate_big.py -o results_simulation_va1.txt simulation_lifestate_va1

#for f in `ls |grep tar.bz2`
#do
#	(python ~/software/benchtools/analyze/extract_log.py -p -f ~/Documents/source/verivita/benchtools_setup/filters/simulate_big.py -o results_${f}.txt $f)&
#done
#
#for f in `ls |grep txt`
#do
#	BLOCK=`grep -c "result Block" $f`
#	READERROR=`grep -c "result ReadError" $f`
#	TIMEOUT=`grep -c "time Timeout" $f`
#	UNK=`grep -c "result ? time ?" $f`
#	echo "--------------------------"
#	echo $f
#	echo "block: $Block"
#	echo "timeout: $TIMEOUT"
#	echo "read error: $READERROR"
#	echo "unknown: $UNK"
#done
