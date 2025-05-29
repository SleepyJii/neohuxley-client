
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import uuid

from utils.config import APP_ROOT
from db.database import Database

import json
import os
from pathlib import Path
import uuid

router = APIRouter()


@router.post("/outbox/{username}")
async def post_outbox(username: str, request: Request):
    content = await request.json()
    
    host = request.base_url.hostname
    activity_uuid = str(uuid.uuid4())
    activity_id = f"https://{host}/activities/{activity_uuid}"

    activity = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": activity_id,
        "type": "Create",
        "actor": f"https://{host}/users/{username}",
        "published": datetime.utcnow().isoformat() + "Z",
        "to": ["https://www.w3.org/ns/activitystreams#Public"],
        "object": {
            "id": f"{activity_id}#note",
            "type": "Note",
            "attributedTo": f"https://{host}/users/{username}",
            "content": content.get("content", ""),
            "published": datetime.utcnow().isoformat() + "Z",
            "to": ["https://www.w3.org/ns/activitystreams#Public"]
        }
    }

    Database.store(activity, username, 'outbox', _uuid=activity_uuid)

    # TODO: also should presumably actually send the object wherever

    # Fan out to followers?
    # THERE WILL BE NO FOLLOWERS IN THIS DOJO

    return JSONResponse(content=activity, media_type="application/activity+json")



