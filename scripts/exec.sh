#!/bin/bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

CID_FILE="$SCRIPT_DIR/../state/container.cid"

if [[ ! -f "$CID_FILE" ]]; then
  echo "❌ No running NeoHuxley-Client cid file found."
  exit 1
fi

CID=$(cat "$CID_FILE")

if [[ $# -eq 0 ]]; then
  # No arguments passed — default to interactive shell
  docker exec -it "$CID" bash
else
  # Run provided command inside the container
  docker exec -it "$CID" "$@"
fi
