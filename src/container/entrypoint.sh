#!/bin/bash


# launch activitypub server
./launch_activitypub.sh  > /var/log/activitypub.log 2>&1 &

# launch / connect to mesh via tailscale
./launch_tailscale.sh > /var/log/tailscale.log 2>&1 &

# setup firewall (includes dante SOCKS5)
./setup_firewall_routing.sh > /var/log/firewall.log 2>&1 &

# never kill this script, keeps container alive
tail -f /dev/null
