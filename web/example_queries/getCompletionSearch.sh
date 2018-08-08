#!/bin/bash
curl -X GET http://localhost:9000/completion_search -d "@callin_hole.json" -H "Content-Type: application/JSON"

