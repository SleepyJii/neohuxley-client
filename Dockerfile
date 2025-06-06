FROM alpine:3.19

RUN apk add --no-cache curl iptables ip6tables bash dante-server socat


# Install Tailscale 1.66.4
RUN curl -fsSL https://pkgs.tailscale.com/stable/tailscale_1.66.4_amd64.tgz | tar -xz \
  && mv tailscale*/tailscale tailscale*/tailscaled /usr/sbin/

# Create working dirs
RUN mkdir -p /var/lib/tailscale /dev/net \
  && mknod /dev/net/tun c 10 200 || true

# Set up entrypoint script, all else from src/tailscale_container
COPY src/tailscale_container/* /
RUN chmod +x /tailscale_entrypoint.sh
RUN chmod +x /container_firewall.sh

# copy dante SOCKS5 config
COPY config/container/dante.conf /etc/dante.conf

# Handle HTTPS certificates
COPY certs/* /usr/local/share/ca-certificates/
RUN update-ca-certificates

CMD /tailscale_entrypoint.sh > /var/log/tailscale.log 2>&1

