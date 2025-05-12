from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from utils.signatures import verify_http_signature

router = APIRouter()

#async def post_inbox(username: str, request: Request):
#    activity = await request.json()
    # TDO: Verify HTTP Signature
    # TDO: Store activity in database
#    return JSONResponse(content={"status": "Activity received"}, status_code=202)


@router.post("/inbox/{username}")
async def post_inbox(username: str, request: Request):

    signature = request.headers.get('Signature')
    if not signature:
        # UNSIGNED, HANDLE
        pass # ... you know what, i dont give a shit if you dont sign it
    else:
        # SIGNED, HANDLE
        await verify_http_signature(request)

    body = await request.json()

    # TODO: Process activity, store, respond
    
    return {"status": "Activity received"}



