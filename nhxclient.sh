#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CID_FILE="$SCRIPT_DIR/state/container.cid"

# self-aliase, registers if sourced
alias nhxclient="$SCRIPT_DIR/nhxclient.sh"


# Helper: check container is running
function container_status() {
    if [[ -f "$CID_FILE" ]]; then
        CID=$(cat "$CID_FILE")
        if docker ps -q --no-trunc | grep -q "$CID"; then
            return 0
        fi
    fi
    return 1
}

# Helper: get container CID or error
function get_cid() {
    if [[ -f "$CID_FILE" ]]; then
        cat "$CID_FILE"
    else
        echo "❌ No running container (tsclient.cid not found)." >&2
        exit 1
    fi
}


# Helper: get tailscale status from container
function get_tailscale_status() {
    CID=$(get_cid)
    docker exec "$CID" tailscale status 2>/dev/null
}

function get_activitypub_status() {
    CID=$(get_cid)
    UVICORN_PROC=$(docker exec "$CID" pgrep -af "uvicorn.*activitypub_server:app")
    if [[ -n "$UVICORN_PROC" ]]; then
        return 0
    else
        return 1
    fi
}


# Command router
case "$1" in
  launch)
    shift
    "$SCRIPT_DIR/scripts/launch.sh" "$@"
    ;;
  kill)
    shift
    "$SCRIPT_DIR/scripts/kill.sh" "$@"
    ;;
  shell)
    shift
    "$SCRIPT_DIR/scripts/exec.sh" "$@"
    ;;
  chatter)
    shift
    "$SCRIPT_DIR/scripts/chatter.sh" "$@"
    ;;
  tailscale)
    shift
    "$SCRIPT_DIR/scripts/exec.sh" tailscale "$@"
    ;;
  status)
    echo -e "\n🌐 \e[1mNeoHuxley Client Status\e[0m\n"
    if container_status; then
        echo -e "✅ Docker container \e[32mrunning\e[0m (CID: $(get_cid))"
        echo -e "\n🔐 \e[1mTailscale Status\e[0m:"
        get_tailscale_status

        echo -e "\n🔐 \e[1mActivityPub Status\e[0m:"
	    if get_activitypub_status; then
		echo -e "✅ \e[32mRunning\e[0m"
	    else
		echo -e "❌ \e[31mNot running\e[0m" 
	    fi
    else
        echo -e "❌ Docker container \e[31mnot running\e[0m."
    fi
    echo ""
    echo "Usages: nhxclient [launch|shell|chatter|tailscale|status]"
    echo ""
    ;;
  *)
    echo "Usages: nhxclient [launch|shell|chatter|tailscale|status]"
    ;;
esac

#alias nhxclient-tailscale="$SCRIPT_DIR/scripts/cli.sh"
#alias nhxclient="$SCRIPT_DIR/scripts/exec.sh"
#alias nhxclient-launch="$SCRIPT_DIR/scripts/launch.sh"
#alias nhxclient-chatter="$SCRIPT_DIR/scripts/chatter.sh $@"


