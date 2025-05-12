from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse

router = APIRouter()

@router.get("/.well-known/webfinger")
async def webfinger(resource: str, request: Request):
    # Expect resource like acct:alice@yourdomain.com
    if not resource.startswith("acct:"):
        return JSONResponse(status_code=400, content={"error": "Bad request"})

    username = resource.split("acct:")[1].split("@")[0]
    host = request.base_url.hostname

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
