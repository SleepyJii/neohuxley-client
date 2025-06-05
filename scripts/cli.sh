#!/bin/bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

CID_FILE="$SCRIPT_DIR/../tsclient.cid"

if [[ ! -f "$CID_FILE" ]]; then
  echo "Error: No running Tailscale container found."
  exit 1
fi

CID=$(cat "$CID_FILE")

# Run tailscale CLI inside the container, passing all args
docker exec -it "$CID" tailscale "$@"

