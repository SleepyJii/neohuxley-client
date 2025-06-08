from routes import actor, webfinger, inbox, outbox, chatter
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
from starlette.websockets import WebSocketState
from workers.outbox_worker import preload_unsent_outbox, outbox_worker
import asyncio


app = FastAPI()


# Kick off outbox_worker
@app.on_event("startup")
async def startup_event():
    await preload_unsent_outbox()  # Load any unsent activities into queue
    asyncio.create_task(outbox_worker())


# ActivityPub endpoints. These really should just pass around DB info
app.include_router(actor.router)
app.include_router(webfinger.router)
app.include_router(inbox.router)
app.include_router(outbox.router)
app.include_router(chatter.router)


# WebSocket endpoint for simple chat
@app.websocket("/chatter")
async def websocket_endpoint(websocket: WebSocket, target: str = Query(...)):
    # Only accept connections from localhost
    if websocket.client.host not in ("127.0.0.1", "::1"):
        await websocket.close(code=1008)  # Policy violation
        return

    await websocket.accept()
    print(f'Client connected with target={target}')

    try:
        while True:
            data = await websocket.receive_text()
            print(f'Recieved from {target}: {data}')
            await websocket.send_text(f"[send to {target}] You said: {data}")
    except WebSocketDisconnect:
        print(f"Client with target={target} disconnected")

