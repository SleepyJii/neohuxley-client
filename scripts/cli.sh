#!/bin/bash
set -e

CID_FILE="./tsclient.cid"

if [[ ! -f "$CID_FILE" ]]; then
  echo "Error: No running Tailscale container found."
  exit 1
fi

CID=$(cat "$CID_FILE")

# Run headscale CLI inside the container, passing all args
docker exec -it "$CID" tailscale "$@"

