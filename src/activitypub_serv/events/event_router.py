# events/event_router.py

import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager


class EventRouter:
    def __init__(self):
        self.subscribers = defaultdict(list)

    def subscribe(self, key: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.subscribers[key].append(queue)
        return queue

    def subscribe_queue(self, key: str, qu: asyncio.Queue):
        self.subscribers[key].append(qu)

    async def publish(self, key: str, message: dict):
        for queue in self.subscribers.get(key, []):
            await queue.put(message)

    def unsubscribe(self, key: str, queue: asyncio.Queue):
        self.subscribers[key].remove(queue)

    @asynccontextmanager
    async def subscription(self, key: str):
        queue = asyncio.Queue()
        self.subscribers[key].append(queue)
        try:
            yield queue
        finally:
            self.subscribers[key].remove(queue)
            if not self.subscribers[key]:
                del self.subscribers[key]  # Optional cleanup

# global, other submodules can just import
event_router = EventRouter()

