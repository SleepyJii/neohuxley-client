from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse


router = APIRouter()


# i dont need no fockin user db, I am the user

@router.get("/users/{username}", response_class=JSONResponse)
async def get_actor(username: str, request: Request):
    host = request.base_url.hostname
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
            "publicKeyPem": "" #TODO: load user's public key
        }
    }
    return JSONResponse(content=actor, media_type="application/activity+json")

