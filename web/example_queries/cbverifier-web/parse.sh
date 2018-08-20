#!/bin/bash
curl -X POST http://localhost:5000/parse_ls -d "@${1}" -H "Content-Type: application/JSON"

