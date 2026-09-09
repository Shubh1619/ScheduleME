#!/bin/sh

echo "==> starting backend (uvicorn :8765)"
uvicorn app.main:app --host 0.0.0.0 --port 8765 &
API_PID=$!
echo "==> backend pid $API_PID"

echo "==> starting frontend (next start :${PORT:-10000})"
cd /app/frontend || { echo "FAILED to cd /app/frontend"; exit 1; }
next start -p "${PORT:-10000}" -H 0.0.0.0 &
WEB_PID=$!
echo "==> frontend pid $WEB_PID"

trap 'kill "$API_PID" "$WEB_PID" 2>/dev/null' TERM INT

wait "$API_PID"
echo "==> backend exited ($?)"
wait "$WEB_PID"
echo "==> frontend exited ($?)"