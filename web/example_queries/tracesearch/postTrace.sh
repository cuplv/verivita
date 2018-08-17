#!/bin/bash
curl -X POST http://localhost:9000/get_traces_methods -d "@${1}" -H "Content-Type: application/JSON"

