from datetime import datetime
import uuid
import json
from db.database import Database
from workers.outbox_worker import delivery_queue

db = Database()


def create_note_activity(
    username: str,
    content: str,
    host: str,
    send_to: list[str] = None,
    addressed_to: list[str] = None,
    submit=True
) -> dict:
    activity_uuid = str(uuid.uuid4())
    activity_id = f"http://{host}/activities/{activity_uuid}"

    send_to = send_to or ["https://www.w3.org/ns/activitystreams#Public"]
    addressed_to = addressed_to or send_to  # fallback if not specified

    activity = {
        "@context": "https://www.w3.org/ns/activitystreams",
        #        "id": activity_id,
        "type": "Create",
        "actor": f"http://{host}/users/{username}",
        "published": datetime.utcnow().isoformat() + "Z",
        "to": send_to,
        "object": {
            "id": f"{activity_id}#note",
            "type": "Note",
            "attributedTo": f"http://{host}/users/{username}",
            "content": content,
            "published": datetime.utcnow().isoformat() + "Z",
            "to": addressed_to
        }
    }

    if submit:
        db.insert_outbox(json.dumps(activity), activity_id)
        delivery_queue.put_nowait(activity_id)

    return activity

def create_note(username: str, content: str, to: str, host='127.0.0.1:8000'):
    # simple utility for sending messages from local
    return create_note_activity(username, content, host, [to], [to], submit=False)

