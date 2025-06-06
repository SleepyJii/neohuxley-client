#!/bin/bash


# setup firewall
./container_firewall.sh


/usr/sbin/tailscaled --state=/var/lib/tailscale/tailscaled.state &

# Wait for the Tailscale daemon to become ready
until [ -e /var/run/tailscale/tailscaled.sock ]; do
  sleep 0.5
done

echo "hn $TAILSCALE_HOSTNAME  ls $TAILSCALE_LOGIN_SERVER  ak $TAILSCALE_AUTH_KEY"

if [[ -n "$TAILSCALE_AUTH_KEY" ]]; then
  echo "🔐 Running tailscale up with auth key..."
  tailscale up \
    --hostname "$TAILSCALE_HOSTNAME" \
    --login-server "$TAILSCALE_LOGIN_SERVER" \
    --auth-key "$TAILSCALE_AUTH_KEY" \
    --accept-routes
else
  echo "🔁 Running tailscale up without auth key (reusing identity)..."
  tailscale up \
    --hostname "$TAILSCALE_HOSTNAME" \
    --login-server "$TAILSCALE_LOGIN_SERVER" \
    --accept-routes
fi


