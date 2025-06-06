from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from events.event_router import event_router
from db.database import Database
import uuid
from datetime import datetime
import json
import contextlib
import asyncio


router = APIRouter()
db = Database()


def create_chatter_message(sender: str, recipient: str, content: str, host: str, port: int) -> dict:
    activity_uuid = str(uuid.uuid4())
    activity_id = f"http://{host}:{port}/activities/{activity_uuid}"

    return {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": activity_id,
        "type": "Create",
        "actor": f"http://{host}:{port}/users/{sender}",
        "to": [recipient],
        "object": {
            "id": f"{activity_id}#msg",
            "type": "ChatterMsg",
            "attributedTo": f"http://{host}:{port}/users/{sender}",
            "to": [recipient],
            "content": content,
            "published": datetime.utcnow().isoformat() + "Z"
        },
        "published": datetime.utcnow().isoformat() + "Z"
    }





@router.websocket("/chatter")
async def chatter_ws(websocket: WebSocket, target: str = Query(...)):
    await websocket.accept()

    sender = "host"
    host = websocket.url.hostname
    port = websocket.url.port
    sender_uri = f"http://{host}:{port}/users/{sender}"
    recipient_name, recipient_domain = target.split("@")
    recipient_uri = f"http://{recipient_domain}/users/{recipient_name}"

    db = Database()

    # Send chat history
    messages = db.get_private_messages_between(sender_uri, recipient_uri)
    for msg in messages:
        await websocket.send_json(json.loads(msg["data"]))


    user_input_queue = asyncio.Queue()

    # Define and launch input listener
    async def listen_websocket_input():
        try:
            while True:
                text = await websocket.receive_text()
                await user_input_queue.put(text)
        except WebSocketDisconnect:
            pass  # Gracefully end on disconnect
    input_task = asyncio.create_task(listen_websocket_input()) # kick off input listener

    # Listen for both incoming and outgoing DMs
    send_key = f"CHATTER:outb:{sender_uri}->{recipient_uri}"
    recv_key = f"CHATTER:inb:{recipient_uri}->{sender_uri}"

    async with event_router.subscription(send_key) as send_queue:
        async with event_router.subscription(recv_key) as recv_queue:
            try:
                input_task = asyncio.create_task(user_input_queue.get())
                send_task =  asyncio.create_task(send_queue.get())
                recv_task =  asyncio.create_task(recv_queue.get())

                while True:
                    done, _ = await asyncio.wait(
                        [
                            input_task,
                            send_task,
                            recv_task
                        ],
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    for task in done:

                        if input_task in done:
                            result = input_task.result()
                            input_task = asyncio.create_task(user_input_queue.get()) 
                            if isinstance(result, str):
                                # Message sent from WebSocket client
                                activity = create_chatter_message(
                                    sender=sender,
                                    recipient=recipient_uri,
                                    content=result,
                                    host=host,
                                    port=port
                                )
                                activity['chatter_origin'] = 'origin'
                                db.insert_outbox(json.dumps(activity), activity["id"])
                                await event_router.publish('outbox', dict(id=activity['id']))
                                await event_router.publish(send_key, activity)
                        else:
                            was_outb = send_task in done
                            if was_outb:
                                result = send_task.result()
                                send_task = asyncio.create_task(send_queue.get()) 
                            else:
                                result = recv_task.result()
                                recv_task = asyncio.create_task(recv_queue.get())
                            # Inbound or outbound message from queue
                            # we will have recieved the full activity JSON. we want to parse whats relevant
                            if 'chatter_origin' not in result:
                                print('failing cause of',result)
                            if result['chatter_origin'] == 'origin':
                                # I sent it
                                chat_id = 'user'
                            elif result['chatter_origin'] == 'target':
                                # they sent it
                                chat_id = target
                            else:
                                # ?????
                                chat_id = '???'

                            chat_content = result['object']['content']
                            print(f'{send_key if was_outb else recv_key}:[{chat_id}] {chat_content}')
                            await websocket.send_json({'user': chat_id, 'content': chat_content})

            except WebSocketDisconnect:
                pass
            finally:
                input_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await input_task

