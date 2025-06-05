#!/bin/bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR="$(realpath "$SCRIPT_DIR/..")"

CID_FILE="$SCRIPT_DIR/../tsclient.cid"
LOG_FILE="$SCRIPT_DIR/../logs/tsclient.log"
STATE_DIR="$(realpath "$SCRIPT_DIR/../state")"
LOG_DIR="$(realpath "$SCRIPT_DIR/../logs")"

echo "STATE_DIR is $STATE_DIR"
echo "SCRIPT_DIR is $SCRIPT_DIR"

# Create directories if needed
mkdir -p "$STATE_DIR" "$SCRIPT_DIR/../logs"

# Source configuration files
set -a
source "$SCRIPT_DIR/../config/nhxclient.sh"
set +a

# Optional: hostname override
HOSTNAME=${CLIENT_NAME:-$(hostname)}
echo "using CLIENT_NAME $HOSTNAME"

# First-time setup check
FIRST_RUN=false
if [[ ! -f "$STATE_DIR/tailscaled.state" ]]; then
  FIRST_RUN=true
fi

# If first run, validate required environment
if $FIRST_RUN; then
  if [[ -z "$AUTH_KEY" || -z "$LOGIN_SERVER" ]]; then
    echo "❌ First-time run: you must set TAILSCALE_AUTH_KEY and TAILSCALE_LOGIN_SERVER."
    echo "Example:"
    echo "  TAILSCALE_AUTH_KEY=tskey-xxxxx TAILSCALE_LOGIN_SERVER=http://your.headscale:8080 ./launch.sh"
    exit 1
  fi
  echo "🔐 First-time setup: using provided auth key..."
else
  echo "🔁 Existing identity found: skipping auth key."
fi

# Clean up any existing container
docker rm -f neohuxley-client 2>/dev/null || true

docker build --no-cache -t neohuxley-client:local $ROOT_DIR

echo "🚀 Starting Tailscale client container..."

# Build Docker run command dynamically
DOCKER_CMD=(
  docker run --rm -d
  --name neohuxley-client
  --cap-add=NET_ADMIN
  --device /dev/net/tun
  -v "$STATE_DIR:/var/lib/tailscale"
  -v "$LOG_DIR:/var/log"
  -e TAILSCALE_HOSTNAME="$HOSTNAME"
  -e TAILSCALE_LOGIN_SERVER="$LOGIN_SERVER"
  -e TAILSCALE_AUTH_KEY="$AUTH_KEY"
  -p 127.0.0.1:1080:1080
  --add-host=host.docker.internal:host-gateway
)

DOCKER_CMD+=("neohuxley-client:local")

# Run container and write CID
"${DOCKER_CMD[@]}" > "$CID_FILE"

echo "✅ Tailscale client launched. CID: $(cat "$CID_FILE")"

