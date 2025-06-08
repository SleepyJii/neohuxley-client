#!/bin/sh

cd /activitypub

LOG_FILE="/var/log/activitypub.log"
uvicorn activitypub_server:app --host 0.0.0.0 --port 80 --log-level debug > $LOG_FILE 2>&1

while true; do
  echo "➡️  relaunching uvicorn at $(date)" >> "$LOG_FILE"

  uvicorn activitypub_server:app --host 0.0.0.0 --port 80 --log-level debug >> "$LOG_FILE" 2>&1

  echo "⚠️  uvicorn exited at $(date). Restarting in 2 seconds..." >> "$LOG_FILE"
  sleep 2
done


