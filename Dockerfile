FROM python:3.11-alpine

RUN apk add --no-cache curl iptables ip6tables bash dante-server socat build-base libffi-dev


# Install Tailscale 1.66.4
RUN curl -fsSL https://pkgs.tailscale.com/stable/tailscale_1.66.4_amd64.tgz | tar -xz \
  && mv tailscale*/tailscale tailscale*/tailscaled /usr/sbin/

# Create working dirs
RUN mkdir -p /var/lib/tailscale /dev/net \
  && mknod /dev/net/tun c 10 200 || true

# copy ActivityPub server over, install reqs
RUN mkdir /activitypub/
COPY src/activitypub_serv/requirements.txt /activitypub/requirements.txt
RUN pip install --no-cache-dir -r /activitypub/requirements.txt
COPY src/activitypub_serv/ /activitypub/

# copy over built activitypub_chatter TUI
COPY src/activitypub_chatter/target/x86_64-unknown-linux-musl/release/activitypub_chatter /chatter
RUN chmod +x /chatter

# Set up entrypoint script, all else from src/tailscale_container
COPY src/tailscale_container/* /
RUN chmod +x /tailscale_entrypoint.sh
RUN chmod +x /container_firewall.sh
RUN chmod +x /setup_activitypub.sh

# copy dante SOCKS5 config
COPY config/container/dante.conf /etc/dante.conf

# Handle HTTPS certificates
COPY certs/* /usr/local/share/ca-certificates/
RUN update-ca-certificates


CMD /tailscale_entrypoint.sh > /var/log/tailscale.log 2>&1

