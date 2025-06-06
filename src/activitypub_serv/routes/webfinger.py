# routes/webfinger.py

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse

from utils.config import APP_ROOT
from db.database import Database

router = APIRouter()
db = Database()


@router.get("/.well-known/webfinger")
async def webfinger(resource: str, request: Request):

    if not resource.startswith("acct:"):
        return JSONResponse(status_code=400, content={"error": "Bad request"})

    username = resource.split("acct:")[1].split("@")[0]
    host = request.base_url.hostname

    if not db.check_user(username):
        return JSONResponse(status_code=404, content={"error": "User not found"})

    data = {
        "subject": f"acct:{username}@{host}",
        "links": [
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": f"http://{host}/users/{username}"
            }
        ]
    }
    return JSONResponse(content=data)

