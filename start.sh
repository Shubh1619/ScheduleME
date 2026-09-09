#!/bin/sh
set -e

cd /app
uvicorn app.main:app --host 0.0.0.0 --port 8765 &
API_PID=$!

cd /app/frontend
next start -p "${PORT:-3000}" -H 0.0.0.0 &
WEB_PID=$!

trap 'kill $API_PID $WEB_PID 2>/dev/null || true' TERM INT

wait $API_PID
wait $WEB_PID