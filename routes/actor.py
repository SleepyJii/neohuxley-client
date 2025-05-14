
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from utils.config import APP_ROOT

import os
from pathlib import Path

router = APIRouter()


# i dont need no fockin user db, I am the user

@router.get("/users/{username}", response_class=JSONResponse)
async def get_actor(username: str, request: Request):
    host = request.base_url.hostname

    actor_pub_path = Path(APP_ROOT) / 'db' / 'users' / username / f'{username}_pub.pem'
    if not actor_pub_path.exists():
        return JSONResponse(status_code=404, content={"error": "Actor not found"})

    with open(str(actor_pub_path), 'r') as f:
        public_key = f.read()

    actor = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": f"https://{host}/users/{username}",
        "type": "Person",
        "preferredUsername": username,
        "inbox": f"https://{host}/inbox/{username}",
        "outbox": f"https://{host}/outbox/{username}",
        "publicKey": {
            "id": f"https://{host}/users/{username}#main-key",
            "owner": f"https://{host}/users/{username}",
            "publicKeyPem": public_key
        }
    }
    return JSONResponse(content=actor, media_type="application/activity+json")

