#!/bin/bash
rm ./instances/*.txt 2>/dev/null
find -L ~/Documents/data/monkey_traces/ -name "*repaired" > ./instances/allTraces.txt #overwrite old one
#find ~/Documents/data/monkey_traces/ -name "trace-*" >> ./instances/allTraces.txt #append


