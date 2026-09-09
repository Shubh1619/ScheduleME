#!/bin/sh
cd /app || exit 1
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}"