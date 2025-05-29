## NeoHuxley-Client (Dockerized Tailscale + ActivityPub)

This simple server is meant to be self-hosted over a mesh network to handle the self-hosters community interactions.

### design principles
- HACKABLE!
- *extremely* lightweight
- Not intended to host multiple users; baked in assumption that the ServerOwner == User == Client
- Extremely simple data management; rated only for local community subnets
- did I mention HACKABLE?

### current status
prototyping vibe-coded ActivityPub protocol in old-school Huxley VMs

### cool features I would like to try

- RSS activity feed hookup; would be useful to have alerts to phone etc summarizing SubNet community happenings
- IRC-chat plugin; ability to have TUI chat app sending messages over ActivityPub
- subnet aliases; would be cool to maintain multiple "identities" for ActivityPub interactions going through different subnets
