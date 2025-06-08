#!/bin/bash

set -e

## ======== FIREWALL RULES =========
## UNFORTUNATELY, ufw is only debian-based, cant use in alpine
## hence defining firewall rules in raw `iptables` format


# Flush all existing rules
iptables -F
iptables -X

# Set default policies, allow from everywhere (localhost, docker, etc)
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

# .. but Drop all tailscale0 traffic by default
iptables -A INPUT -i tailscale0 -j  DROP

# .. but Allow incoming tailscale SSH (22), HTTP (80 || 8080), and HTTPS (443) traffic
iptables -A INPUT -i tailscale0 -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -i tailscale0 -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -i tailscale0 -p tcp --dport 8080 -j ACCEPT
iptables -A INPUT -i tailscale0 -p tcp --dport 443 -j ACCEPT


# Allow loopback traffic
iptables -A INPUT -i lo -j ACCEPT

# Allow incoming traffic for already established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT



## ======== PORT FORWARDS / ROUTING =========

# send port 22 (SSH) traffic through to the docker host
socat TCP-LISTEN:22,fork TCP:host.docker.internal:22 &



## ========== SOCKS5 DANTE CONFIG ===========

# this should programmatically populate the interface IP for tailscale in dante.conf
while ! ip link show tailscale0 &>/dev/null; do
  echo "⏳ Waiting for tailscale0 interface..."
  sleep 1
done

while true; do
  TAILSCALE_IP=$(ip addr show tailscale0 | grep -oE 'inet\s[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | cut -d' ' -f2)
  if [ -n "$TAILSCALE_IP" ]; then
    break
  fi
  echo "⏳ Waiting for Tailscale IP on tailscale0..."
  sleep 1
done
echo 'tailscale0 IP resolved to ' $TAILSCALE_IP
sed -i "s|__EXTERNAL_IP__|$TAILSCALE_IP|" /etc/dante.conf

# launch SOCKS5 proxy for host -> *.neohuxley.net
exec sockd -f /etc/dante.conf



