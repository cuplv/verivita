#!/bin/bash
while true
do
	if [[ -f "/home/muse/trace-query-1.0-SNAPSHOT/RUNNING_PID" ]]; then rm "/home/muse/trace-query-1.0-SNAPSHOT/RUNNING_PID"; fi
	bash -c "/home/muse/trace-query-1.0-SNAPSHOT/bin/trace-query"
done
