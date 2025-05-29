FROM alpine:3.19

RUN apk add --no-cache curl iptables ip6tables bash

# Install Tailscale
RUN curl -fsSL https://pkgs.tailscale.com/stable/tailscale_1.66.4_amd64.tgz | tar -xz \
  && mv tailscale*/tailscale tailscale*/tailscaled /usr/sbin/

# Create working dirs
RUN mkdir -p /var/lib/tailscale /dev/net \
  && mknod /dev/net/tun c 10 200 || true

# Set up entrypoint script
COPY src/tailscale_container/tailscale_entrypoint.sh /tailscale_entrypoint.sh
RUN chmod +x /tailscale_entrypoint.sh

CMD /tailscale_entrypoint.sh >> /var/log/tailscale.log 2>&1

