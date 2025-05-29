
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse

from utils.config import APP_ROOT

router = APIRouter()

@router.get("/.well-known/webfinger")
async def webfinger(resource: str, request: Request):
    # Expect resource like acct:alice@yourdomain.com
    if not resource.startswith("acct:"):
        return JSONResponse(status_code=400, content={"error": "Bad request"})

    username = resource.split("acct:")[1].split("@")[0]
    host = request.base_url.hostname

    actor_pub_path = Path(APP_ROOT) / 'db' / 'users' / username / f'{username}_pub.pem'
    if not actor_pub_path.exists():
        return JSONResponse(status_code=404, content={"error": "User not found"})

    with open(str(actor_pub_path), 'r') as f:
        public_key = f.read()

    data = {
        "subject": f"acct:{username}@{host}",
        "links": [
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": f"https://{host}/users/{username}"
            }
        ]
    }
    return JSONResponse(content=data)

