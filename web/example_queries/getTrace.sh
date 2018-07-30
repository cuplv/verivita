#!/bin/bash
curl -X POST http://localhost:9000/get_traces -d "@${1}" -H "Content-Type: application/JSON"

