from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/outbox/{username}")
async def post_outbox(username: str, request: Request):
    content = await request.json()
    
    # Build a Create activity for a Note
    # TODO: Save object in DB
    # TODO: Fan out to followers
    host = request.base_url.hostname
    activity_id = f"https://{host}/activities/{str(uuid.uuid4())}"

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

    return JSONResponse(content=activity, media_type="application/activity+json")
