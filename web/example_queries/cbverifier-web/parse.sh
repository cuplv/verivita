#!/bin/bash
curl -X GET http://localhost:5000/parse_ls -d "@${1}" -H "Content-Type: application/JSON"

