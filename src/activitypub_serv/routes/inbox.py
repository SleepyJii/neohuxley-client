
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from utils.signatures import verify_http_signature
from pathlib import Path
from utils.config import APP_ROOT
import re
import json


router = APIRouter()


@router.post("/inbox/{username}")
async def post_inbox(username: str, request: Request):

    signature = request.headers.get('Signature')
    if not signature:
        #return JSONResponse(
        #    status_code=401,
        #    content={"error": "Missing HTTP Signature"}
        #)
        pass
    else:
        try:
            await verify_http_signature(request)
        except Exception as e:
            print(e)
            return JSONResponse(
                status_code=403,
                content={"error": "Invalid HTTP Signature"}
            )

    body = await request.json()

    activity_id = body.get('id')
    sss = re.findall(r'^https://([^/]*)/activities/(.*)$', str(activity_id))
    if sss == []:
        raise Exception('Unexpected `activity_id` format', activity_id)
    else:
        simplehost, _uuid = sss[-1]
        

    #hacky storage
    user_inb_dir = Path(APP_ROOT) / 'db' / 'inbox' / username
    if not user_inb_dir.exists():
        return JSONResponse(status_code=404, content={"error": "Actor not found"})

    with open(str(user_inb_dir / f'{simplehost}+{_uuid}.json'), 'w', encoding='utf8') as json_file:
        json.dump({'headers': dict(request.headers), 'body': body}, json_file, allow_nan=True)

    return {"status": "Activity received"}



