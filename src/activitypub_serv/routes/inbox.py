# routes/inbox.py

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from utils.signatures import verify_signature_header
from pathlib import Path
from utils.config import APP_ROOT
from db.database import Database
from events.event_router import event_router
import re
import json


router = APIRouter()
db = Database()

async def _recieved_eventhooks(activity):
    # put event_router hooks here if desired

    ## special hook for /chatter 
    if activity['type'] == 'Create':
        if activity['object']['type'] == 'ChatterMsg':
            fromuser = activity['actor']
            touser = activity['object']['to'][0] # should only be one for CHATTER
            # I can recklessly edit activity here cause its just for chatter now
            activity['chatter_origin'] = 'target'
            await event_router.publish(f'CHATTER:inb:{fromuser}->{touser}', activity)


@router.post("/inbox/{username}")
async def post_inbox(username: str, request: Request):

    signature = request.headers.get('Signature')
    if not signature:
        #return JSONResponse(
        #    status_code=401,
        #    content={"error": "Missing HTTP Signature"}
        #)
        print("\t[warning] inbox recieved unsigned activity")
    else:
        try:
            await verify_signature_header(request)
        except Exception as e:
            print(e)
            return JSONResponse(
                status_code=403,
                content={"error": "Invalid HTTP Signature"}
            )

    body = await request.json()
    activity_id = body.get('id', None)
    if not activity_id:
        return JSONResponse(status_code=400, content={"error", "Posted activity has no id"})

    if not db.check_user(username):
        return JSONResponse(status_code=404, content={"error": "Actor not found"})

    db.insert_inbox(json.dumps(body), activity_id)
    await _recieved_eventhooks(body)

    return {"status": "Activity received"}



