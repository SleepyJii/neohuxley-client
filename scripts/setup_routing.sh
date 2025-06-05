#!/usr/bin/env bash
set -euo pipefail

DOMAIN="neohuxley.net"
IPSET_NAME="neohuxley"
CONFIG_DIR="./config/host"
DNSMASQ_SRC="$CONFIG_DIR/dnsmasq.neohuxley.conf"
DNSMASQ_DEST="/etc/dnsmasq.d/$IPSET_NAME.conf"
REDSOCKS_SRC="$CONFIG_DIR/redsocks.conf"
REDSOCKS_DEST="/etc/redsocks.conf"

echo "📦 Installing required packages..."
sudo apt-get update
sudo apt-get install -y dnsmasq ipset iptables redsocks

echo "📡 Ensuring ipset '$IPSET_NAME' exists..."
sudo ipset create "$IPSET_NAME" hash:ip -exist

# Prompt user before overwriting dnsmasq config
if [ ! -f "$DNSMASQ_DEST" ]; then
  echo "📝 Copying dnsmasq config for $DOMAIN..."
  sudo cp "$DNSMASQ_SRC" "$DNSMASQ_DEST"
else
  echo "✅ Existing dnsmasq config detected at $DNSMASQ_DEST — not overwriting."
fi

echo "🔁 Restarting dnsmasq..."
sudo systemctl restart dnsmasq


# Prompt before touching redsocks config
if [ ! -f "$REDSOCKS_DEST" ]; then
  echo "📝 Copying redsocks config..."
  sudo cp "$REDSOCKS_SRC" "$REDSOCKS_DEST"
else
  echo "✅ Existing redsocks config detected at $REDSOCKS_DEST — not overwriting."
fi

echo "🚀 Starting redsocks..."
sudo pkill redsocks || true
sudo redsocks -c "$REDSOCKS_DEST"


echo "🧱 Setting up iptables chain 'REDSOCKS' (non-destructive)..."
sudo iptables -t nat -N REDSOCKS 2>/dev/null || true

# Append only if not present
if ! sudo iptables -t nat -C REDSOCKS -p tcp -m set --match-set "$IPSET_NAME" dst -j REDIRECT --to-ports 12345 2>/dev/null; then
  sudo iptables -t nat -A REDSOCKS -p tcp -m set --match-set "$IPSET_NAME" dst -j REDIRECT --to-ports 12345
fi

if ! sudo iptables -t nat -C OUTPUT -p tcp -m owner ! --uid-owner 0 -j REDSOCKS 2>/dev/null; then
  sudo iptables -t nat -A OUTPUT -p tcp -m owner ! --uid-owner 0 -j REDSOCKS
fi


echo "🎉 Transparent routing for *.$DOMAIN is now active!"

