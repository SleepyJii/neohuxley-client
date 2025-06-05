#!/bin/bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

CID_FILE="$SCRIPT_DIR/../tsclient.cid"

if [[ ! -f "$CID_FILE" ]]; then
  echo "❌ No running NeoHuxley-Client cid file found."
  exit 1
fi

CID=$(cat "$CID_FILE")

# Open an interactive shell inside the container
docker exec -it "$CID" bash

