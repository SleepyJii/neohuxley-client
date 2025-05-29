from fastapi import FastAPI
from routes import actor, webfinger, inbox, outbox

app = FastAPI()

app.include_router(actor.router)
app.include_router(webfinger.router)
app.include_router(inbox.router)
app.include_router(outbox.router)
