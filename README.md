# NeoHuxley-Client (Dockerized Tailscale + ActivityPub)
This project is meant to contain everything necessary for on-the-fly membership in a mesh net, with ActivityPub social media integrations.

## Tailscale Docker Container
### motivation
It is assumed that the target mesh network will be done via Headscale.
Unfortunately Headscale does not support multiple subnets, meaning that there can only be one set of DNS rules for all clients, controlled by the Headscale node. This means that all clients would have *all* local ports exposed on the network by default. To avoid that ugliness, or the lesser ugliness of custom firewall rules, the Dockerfile in this container + `src/tailscale_container` handles tailscale membership, acting as a de facto sandbox.

### usage
(2025-05-29) Easiest interfaces provided by `source script_aliases`. You'll need docker to be installed.
For first time connection to a Headscale subnet,
- source `script_aliases` in the project root
- run `CLIENTNAME=$USER_ALIAS LOGIN_SERVER=http://$HEADSCALE_IP:8080 AUTH_KEY=$PROVIDED_AUTHKEY nhxclient-launch`

The launch command will mount state dirs in the project root. This means you can kill your docker container if necessary, and in the future can skip the `AUTH_KEY` so long as you connected successfully in the first place.

When the tailscale container is running, a file will be saved into project root storing the relevant docker CID. Other aliases will use this file for interacting with the container.

`nhxclient $ARGS`: while the container is running this is equivalent to running `tailscale $ARGS` within the docker container, AKA can check connection status with `nhxclient status`

`nhxclient-exec`: opens bash within the running docker container for poking around


## ActivityPub Solo Server
This simple server is meant to be self-hosted over a mesh network to handle the self-hosters community interactions.

### motivation
Once you and your mates can connect to each other, it would be nice to have easily extensible messaging functionality.
ActivityPub is flexible enough to allow everything from simple DMs to full forum interactivity. The typing system is itself extendable, so this can really be worked into anything by hacky folk.

### design principles
- HACKABLE!
- *extremely* lightweight
- Not intended to host multiple users; baked in assumption that the ServerOwner == User == Client
- Extremely simple data management; rated only for local community subnets
- did I mention HACKABLE?

### current status

finish implementing! right now its half-finished

prototyping vibe-coded ActivityPub protocol in old-school Huxley VMs

### cool features I would like to try
- RSS activity feed hookup; would be useful to have alerts to phone etc summarizing SubNet community happenings
- IRC-chat plugin; ability to have TUI chat app sending messages over ActivityPub
- subnet aliases; would be cool to maintain multiple "identities" for ActivityPub interactions going through different subnets
- Minecraft server with ActivityPub authentication?
- P2P file sharing protocols with ActivityPub handshakes?
- ActivityPub centralized Karma system for hosting services on the subnet? Voting rights on headscale server??
