#!/bin/bash
curl -X GET http://localhost:9000/traces_search/rank -d "@${1}" -H "Content-Type: application/JSON"

