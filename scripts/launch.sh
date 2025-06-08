#!/bin/bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR="$(realpath "$SCRIPT_DIR/..")"

LOG_FILE="$SCRIPT_DIR/../logs/tsclient.log"
STATE_DIR="$(realpath "$SCRIPT_DIR/../state")"
LOG_DIR="$(realpath "$SCRIPT_DIR/../logs")"
CID_FILE="$STATE_DIR/container.cid"

echo "STATE_DIR is $STATE_DIR"
echo "SCRIPT_DIR is $SCRIPT_DIR"

function container_status() {
    if [[ -f "$CID_FILE" ]]; then
        CID=$(cat "$CID_FILE")
        if docker ps -q --no-trunc | grep -q "$CID"; then
            return 0
        fi
    fi
    return 1
}

# Helper: get container CID or error
function get_cid() {
    if [[ -f "$CID_FILE" ]]; then
        cat "$CID_FILE"
    else
        exit 1
    fi
}
if container_status; then
    echo "🛑 launch blocked, because nhxclient container $CID is still alive"
    exit 1
fi

# Create directories if needed
mkdir -p "$STATE_DIR" "$SCRIPT_DIR/../logs"

# Source configuration files
set -a
source "$SCRIPT_DIR/../nhxclient.config"
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

docker build -t neohuxley-client:local $ROOT_DIR --build-arg NHXCLIENT_APPROVED_BUILD=yes

echo "🚀 Starting Tailscale client container..."
# making sure $STATE_DIR/activitypub.sqlite is understood to be a file
touch "$STATE_DIR/activitypub.sqlite"

# Build Docker run command dynamically
DOCKER_CMD=(
  docker run --rm -d
  --name neohuxley-client
  --cap-add=NET_ADMIN
  --device /dev/net/tun
  -v "$STATE_DIR:/var/lib/tailscale"
  -v "$STATE_DIR/activitypub.sqlite:/activitypub/activitypub.sqlite"
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

