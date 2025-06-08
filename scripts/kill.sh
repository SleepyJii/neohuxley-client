#!/bin/bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

CID_FILE="$SCRIPT_DIR/../state/container.cid"

if [[ ! -f "$CID_FILE" ]]; then
  echo "❌ No running NeoHuxley-Client cid file found."
  exit 1
fi

function container_status() {
    if [[ -f "$CID_FILE" ]]; then
        CID=$(cat "$CID_FILE")
        if docker ps -q --no-trunc | grep -q "$CID"; then
            return 0
        fi
    fi
    return 1
}

if container_status; then
    CID=$(cat "$CID_FILE")
    echo "Running \`docker kill\` on the nhxclient container.."
    echo "🛑 stopping nhxclient container $CID..."
    docker kill "$CID"
    echo "✅ nhxclient container stopped and cid file removed."
else
    echo "❌ no running nhxclient container found."
fi

