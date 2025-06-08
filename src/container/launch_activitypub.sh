#!/bin/sh

cd /activitypub
exec uvicorn main:app --host 0.0.0.0 --port 80 > /var/log/activitypub.log 2>&1

