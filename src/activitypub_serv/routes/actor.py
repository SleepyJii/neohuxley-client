# routes/actor.py

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from utils.config import APP_ROOT
from db.database import Database

import os
from pathlib import Path


router = APIRouter()
db = Database()


@router.get("/users/{username}", response_class=JSONResponse)
async def get_actor(username: str, request: Request):
    host = request.base_url.netloc


    if not db.check_user(username):
        return JSONResponse(status_code=404, content={"error": "Actor not found"})


    keys = db.get_keys(username)
    if not keys or not keys.get('public_key'):
        return JSONResponse(status_code=500, content={"error": "Missing public key"})

    actor = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": f"http://{host}/users/{username}",
        "type": "Person",
        "preferredUsername": username,
        "inbox": f"http://{host}/inbox/{username}",
        "outbox": f"http://{host}/outbox/{username}",
        "publicKey": {
            "id": f"http://{host}/users/{username}#main-key",
            "owner": f"http://{host}/users/{username}",
            "publicKeyPem": keys['public_key']
        }
    }
    return JSONResponse(content=actor, media_type="application/activity+json")

