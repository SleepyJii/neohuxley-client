
#!/bin/bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

CID_FILE="$SCRIPT_DIR/../state/container.cid"

if [[ ! -f "$CID_FILE" ]]; then
  echo "Error: No running Tailscale container found."
  exit 1
fi

CID=$(cat "$CID_FILE")

TS_HOSTNAME=$(docker exec "$CID" printenv TAILSCALE_HOSTNAME)

if [[ -z "$TS_HOSTNAME" ]]; then
    echo "Error: TAILSCALE_HOSTNAME not set inside container."
    exit 1
fi

# Parse single arg like user@domain into --target
if [[ $# -ne 1 ]]; then
    echo "Usage: chatter.sh user@domain"
    exit 1
fi


RAW_TARGET="$1"
# Add "host@" prefix if missing '@'
if [[ "$RAW_TARGET" != *@* ]]; then
    RAW_TARGET="host@$RAW_TARGET"
fi

TARGET_ARG="--target=$RAW_TARGET"
HOST_ARG="--host=${TS_HOSTNAME}.neohuxley.net"


exec "$SCRIPT_DIR/exec.sh" "/chatter" "$HOST_ARG" "$TARGET_ARG"

