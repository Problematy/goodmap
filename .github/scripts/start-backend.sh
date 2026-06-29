#!/bin/bash
set -e

# Generic Background Process Starter
# Usage: start-backend.sh <log-file> <pid-file> <startup-wait-seconds> <command...>

LOG_FILE="$1"
PID_FILE="$2"
STARTUP_WAIT="${3:-5}"
shift 3
COMMAND="$@"

if [ -z "$LOG_FILE" ] || [ -z "$PID_FILE" ] || [ -z "$COMMAND" ]; then
  echo "Error: Missing required arguments"
  echo "Usage: start-backend.sh <log-file> <pid-file> <startup-wait-seconds> <command...>"
  exit 1
fi

echo "Starting backend with command:"
echo "  COMMAND: $COMMAND"
echo "  LOG_FILE: $LOG_FILE"
echo "  PID_FILE: $PID_FILE"
echo "  STARTUP_WAIT: ${STARTUP_WAIT}s"

# Wait for port 5000 to be available (up to 30 seconds)
PORT=5000
echo "Checking if port $PORT is available..."
for i in {1..60}; do
  if ! lsof -ti:$PORT >/dev/null 2>&1 && ! netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
    echo "Port $PORT is available"
    break
  fi
  if [ $i -eq 60 ]; then
    echo "ERROR: Port $PORT is still in use after 30 seconds. Processes using it:"
    lsof -ti:$PORT 2>/dev/null || true
    netstat -tuln 2>/dev/null | grep ":$PORT " || true
    exit 1
  fi
  if [ $((i % 10)) -eq 0 ]; then
    echo "Still waiting for port $PORT to be released... (${i}/60)"
  fi
  sleep 0.5
done

# Run the command
eval "$COMMAND" > "$LOG_FILE" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$PID_FILE"
disown $BACKEND_PID

# Wait for startup
sleep "$STARTUP_WAIT"

# Check if process started successfully
if ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "Backend failed to start. Log:"
  cat "$LOG_FILE"
  exit 1
fi

echo "Backend started successfully with PID $(cat "$PID_FILE")"
