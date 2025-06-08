FROM python:3.11-alpine

ARG NHXCLIENT_APPROVED_BUILD
RUN test "$NHXCLIENT_APPROVED_BUILD" = "yes" || (echo >&2 "❌ Do not build neohuxley-client naively! Source 'script_aliases' and run 'nhxclient-launch' instead!!" && exit 1)


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

# Set up entrypoint script, all else from src/container
COPY src/container/* /
RUN chmod +x /entrypoint.sh
RUN chmod +x /launch_tailscale.sh
RUN chmod +x /launch_activitypub.sh
RUN chmod +x /setup_firewall_routing.sh
RUN mv /dante.conf /etc/dante.conf  # dante SOCKS5 config

# Handle HTTPS certificates
COPY certs/* /usr/local/share/ca-certificates/
RUN update-ca-certificates


CMD /entrypoint.sh > /var/log/entrypoint.log 2>&1

