#!/bin/bash
set -e

CID_FILE="./tsclient.cid"

if [[ ! -f "$CID_FILE" ]]; then
  echo "❌ No running NeoHuxley-Client cid file found."
  exit 1
fi

CID=$(cat "$CID_FILE")

# Open an interactive shell inside the container
docker exec -it "$CID" bash

