#!/bin/bash
./get.sh
PYTHONPATH=$PYTHONPATH:/Users/s/software/benchtools/exec/
python /Users/s/Documents/source/verivita/benchtools_setup/scripts/statusCheck/simCheck.py db_simulate
