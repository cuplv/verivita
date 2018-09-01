#!/bin/bash
ulimit -Sv $MEM_LIMIT #5G memory limit
while true
do
	timeout $TIME_LIMIT python /home/muse/verivita/app/verify_task.py
	sleep 3
done
