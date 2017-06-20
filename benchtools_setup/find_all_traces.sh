#!/bin/bash
rm ./instances/*.txt 2>/dev/null
find -L /home/ubuntu/Documents/data/fdroid_monkey -name "*repaired" > ./instances/allTraces.txt #overwrite old one
find -L /home/ubuntu/Documents/data/monkey_traces -name "*repaired" >> ./instances/allTraces.txt #overwrite old one


