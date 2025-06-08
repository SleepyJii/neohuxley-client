import asyncio
import json
import httpx
import email
from db.database import Database
from utils.signatures import create_signature_header
from events.event_router import event_router

db = Database()
delivery_queue = asyncio.Queue() # this will be pushed to by others when appropriate
event_router.subscribe_queue('outbox', delivery_queue) # set up subscription to outb endpoint


async def preload_unsent_outbox():
    unsent = db.get_unsent_outbox(limit=1000)  # Or no limit
    for row in unsent:
        activity = json.loads(row["data"])
        activity_id = activity.get("id")
        if activity_id:
            await delivery_queue.put(dict(id=activity_id))


async def _delivery_eventhooks(delivered_inbx, activity):
    # put event_router hooks here if desired

    ## special hook for /chatter 
    if activity['type'] == 'Create':
        if activity['object']['type'] == 'ChatterMsg':
            fromuser = activity['actor']
            touser = delivered_inbx
            # I can recklessly edit activity here cause its just for chatter now
            activity['chatter_origin'] = 'origin'
            await event_router.publish(f'CHATTER:{fromuser}->{touser}', activity)


async def resolve_inbox(actor_url: str) -> str | None:
    try:
        async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
            resp = await client.get(
                    actor_url,
                    headers={"Accept": "application/activity+json"},
                )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("inbox")
    except Exception as e:
        print(f"[resolve_inbox] Failed to resolve {actor_url}: {e}")
    return None


async def outbox_worker():
    while True:
        event = await delivery_queue.get()
        activity_id = event['id']

        try:
            row = db.get_outbox_by_activity_id(activity_id)
            if not row or row["delivered"]:
                continue

            activity = json.loads(row["data"])
            localactor_uri = activity['actor']
            localactor = localactor_uri[localactor_uri.rfind('/users/')+7:]

            inboxes = []
            for to_addr in activity['to']:
                inbx = await resolve_inbox(to_addr)
                if inbx:
                    inboxes.append(inbx)

            async with httpx.AsyncClient(verify=False) as client:
                for inbox_url in inboxes:
                    remoteactor_uri = inbox_url.replace('/inbox/', '/users/')
                    remoteactor_domain = inbox_url[:inbox_url.rfind('/inbox/')]
                    headers = {
                        "Host": remoteactor_domain,
                        "Date": email.utils.formatdate(usegmt=True),
                        "Content-Type": "application/activity+json",
                    }
                    headers["Signature"] = create_signature_header(
                        request_target=inbox_url,
                        headers=headers,
                        key_id=f"{localactor_uri}#main-key",
                        private_key_pem=db.get_private_key(localactor)
                    )
                    resp = await client.post(
                        inbox_url,
                        json=activity,
                        headers=headers,
                    )
                    if resp.status_code >= 400:
                        raise Exception(f"{resp.status_code} {resp.text}")
                    else:
                        await _delivery_eventhooks(inbox_url, activity)

            db.mark_outbox_delivered(row["id"])
        except Exception as e:
            db.mark_outbox_delivered(row["id"], error=str(e))
            print(f"[Delivery error] {e}")

