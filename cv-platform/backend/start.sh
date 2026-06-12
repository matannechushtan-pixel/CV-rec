#!/bin/bash
set -e

PORT=8001
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "→ Checking for stale process on port $PORT..."
OLD_PID=$(lsof -ti :$PORT 2>/dev/null || true)
if [ -n "$OLD_PID" ]; then
  echo "  Killing stale process PID $OLD_PID"
  kill "$OLD_PID" 2>/dev/null || true
  sleep 1
fi

echo "→ Activating venv..."
source "$SCRIPT_DIR/venv/bin/activate"

echo "→ Starting uvicorn on port $PORT..."
cd "$SCRIPT_DIR"
exec uvicorn main:app \
  --host 127.0.0.1 \
  --port $PORT \
  --reload \
  --log-level info \
  --timeout-keep-alive 30
