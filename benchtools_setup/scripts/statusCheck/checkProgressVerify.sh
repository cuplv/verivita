#!/bin/bash
bash "getV.sh"
PYTHONPATH=$PYTHONPATH:/Users/s/software/benchtools/exec/
python /Users/s/Documents/source/verivita/benchtools_setup/scripts/statusCheck/verifCheck.py db $1
