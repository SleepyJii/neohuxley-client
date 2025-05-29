#!/bin/bash
set -e

CID_FILE="./tsclient.cid"
LOG_FILE="./logs/tsclient.log"
STATE_DIR="./state"

# Optional: hostname override
HOSTNAME=${CLIENTNAME:-$(hostname)}

# Create directories if needed
mkdir -p "$STATE_DIR" ./logs

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

docker build -t neohuxley-client:local .

echo "🚀 Starting Tailscale client container..."

# Build Docker run command dynamically
DOCKER_CMD=(
  docker run --rm -d
  --name neohuxley-client
  --cap-add=NET_ADMIN
  --device /dev/net/tun
  -v "$PWD/$STATE_DIR:/var/lib/tailscale"
  -v "$PWD/logs:/var/log"
  -e TAILSCALE_HOSTNAME="$HOSTNAME"
  -e TAILSCALE_LOGIN_SERVER="$LOGIN_SERVER"
  -e TAILSCALE_AUTH_KEY="$AUTH_KEY"
)

DOCKER_CMD+=("neohuxley-client:local")

# Run container and write CID
"${DOCKER_CMD[@]}" > "$CID_FILE"

echo "✅ Tailscale client launched. CID: $(cat "$CID_FILE")"

