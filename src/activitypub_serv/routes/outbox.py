# routes/outbox.py


from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import uuid

from utils.config import APP_ROOT
from db.database import Database
from workers.outbox_worker import delivery_queue
from events.event_router import event_router

import json
import os
from pathlib import Path
import uuid


router = APIRouter()
db = Database()


def _validate(data):
    _EXP_KEYS = ['@context', 'type', 'actor', 'to', 'object']
    _EXP_OBJ_KEYS = ['type', 'content', 'to']
    for k in _EXP_KEYS:
        if k not in data.keys():
            raise Exception(f'expected response key `{k}`')
    if type(data['object']) is not dict:
        raise Exception('expected `object` to be a dict')
    for k in _EXP_OBJ_KEYS:
        if k not in data['object'].keys():
            raise Exception(f'expected object key `{k}`')


@router.post("/outbox/{username}")
async def post_outbox(username: str, request: Request):

    if not db.check_user(username):
        return JSONResponse(status_code=404, content={"error": "User not found"})

    data = await request.json()
    try:
        _validate(data)
    except Exception as e:
        return JSONResponse(status_code=400, content={'error': str(e)})

    if 'id' not in data:
        # server MUST generate if missing, apparently
        data['id'] = str(uuid.uuid4())
    activity_id = data['id']

    db.insert_outbox(json.dumps(data), activity_id)

    await event_router.publish('outbox', dict(id=activity_id))

    return JSONResponse(content=data, media_type="application/activity+json")


# expected like
#{
#  "@context": "https://www.w3.org/ns/activitystreams",
#  "type": "Create",
#  "actor": "https://example.com/users/alice",
#  "to": ["https://remote.social/users/bob"],
#  "object": {
#    "type": "Note",
#    "content": "Hello world!",
#    "to": ["https://remote.social/users/bob"]
#  }
#}



