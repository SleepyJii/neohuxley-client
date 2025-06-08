# NeoHuxley-Client (Dockerized Tailscale + ActivityPub)
This project is meant to contain everything necessary for on-the-fly membership in a mesh net, with ActivityPub social media integrations.

## USAGE
(2025-06-08)  Main interface script via `nhxclient.sh`. You can also `source nhxclient.sh`, which lets you do `nhxclient` from anywhere. You'll need docker to be installed.
For first time setup (assuming linux or WSL),
- install docker
- source `nhxclient.sh` in the project root
- edit `nhxclient.config` with whatever short alias you want for your computer
- talk to whoever is running the Headscale server and get an `$AUTH_KEY`
- run `AUTH_KEY=$AUTH_KEY nhxclient launch`
- Docker container will build and run in background. You can now do `nhxclient kill` to shutdown and `nhxclient launch` to restart freely without auth or state loss.

After first time setup,
- `nhxclient` or `nhxclient status` will show container status and print usage hints
- `nhxclient launch` to launch if container is dead, `nhxclient kill` to kill container
- `nhxclient shell` opens interactive bash in the container, `nhxclient shell $CMD` runs commands directly
- `nhxclient chatter host@{$SOME_USER_ALIAS}.neohuxley.net` will let you send chat messages to other users in a TUI
  - They will recieve messages so long as they are connected to the network at the time, even if not in the TUI themselves
  - Messages and chat history visible whenever opening `nhxclient chatter` with the relevant person

All state is stored at `$CHECKOUT_PATH/state` (including ActivityPub sqlite DB)
- (...including `container.cid`, which is how scripts keep track of container - if you delete it, make sure to kill container manually)

All logs stored at `$CHECKOUT_PATH/logs`

## Tailscale Docker Container
### motivation
It is assumed that the target mesh network will be done via Headscale.
Unfortunately Headscale does not support multiple subnets, meaning that there can only be one set of DNS rules for all clients, controlled by the Headscale node. This means that all clients would have *all* local ports exposed on the network by default. To avoid that ugliness, or the lesser ugliness of custom firewall rules, the Dockerfile in this container + `src/tailscale_container` handles tailscale membership, acting as a de facto sandbox.

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
- Implemented, though very barebones.
- All data stored in a sqlite database. Activity messages stored in raw JSON str because I'm a madman

## ActivityPub Chatter TUI
Vibe-coded Rust TUI that talks to a WebSocket endpoint on the ActivityPub Solo Server for chat messages
- Expects targets like `host@testclient.neohuxley.net`
  - (by default ActivityPub solo server creates a `host` user)
- Extremely crude, kind of a PoC for what you can do with ActivityPub as a social media layer

## cool features that could be done in extensions
- RSS activity feed hookup; would be useful to have alerts to phone etc summarizing SubNet community happenings
- subnet aliases; would be cool to maintain multiple "identities" for ActivityPub interactions going through different subnets
- Minecraft server with ActivityPub authentication?
- P2P file sharing protocols with ActivityPub handshakes?
- ActivityPub centralized Karma system for hosting services on the subnet? Voting rights on headscale server??
