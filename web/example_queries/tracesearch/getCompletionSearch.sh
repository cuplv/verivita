#!/bin/bash
curl -X GET http://localhost:8080/completion_search -d "@callin_hole.json" -H "Content-Type: application/JSON"

