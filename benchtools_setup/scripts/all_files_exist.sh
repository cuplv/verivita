#!/bin/bash
FILES=`cat $1`
for f in FILES
do
	if [ ! -f $f ]; then
	    echo $f
	fi
done
