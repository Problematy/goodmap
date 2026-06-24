#!/bin/bash
set +e  # Don't exit on errors
set +m  # Disable job control messages

# Stop Goodmap Backend Script
# Usage: stop-backend.sh <pid-file> <config-pattern>

PID_FILE="$1"
CONFIG_PATTERN="$2"

if [ -z "$PID_FILE" ] || [ -z "$CONFIG_PATTERN" ]; then
  echo "Error: Missing required arguments"
  echo "Usage: stop-backend.sh <pid-file> <config-pattern>"
  exit 1
fi

echo "Stopping backend:"
echo "  PID_FILE: $PID_FILE"
echo "  CONFIG_PATTERN: $CONFIG_PATTERN"

# Kill process by PID file if it exists - kill entire process tree recursively
KILLED_BY_PID=false
if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if kill -0 "$PID" 2>/dev/null; then
    echo "Stopping backend with PID $PID and entire process tree"

    # Function to recursively get all descendants
    get_descendants() {
      local pid=$1
      local descendants
      descendants=$(pgrep -P "$pid" 2>/dev/null || true)
      if [ -n "$descendants" ]; then
        echo "$descendants"
        for child in $descendants; do
          get_descendants "$child"
        done
      fi
    }

    # Get all descendants (children, grandchildren, etc.)
    ALL_DESCENDANTS=$(get_descendants "$PID")
    if [ -n "$ALL_DESCENDANTS" ]; then
      # Remove duplicates and sort
      ALL_DESCENDANTS=$(echo "$ALL_DESCENDANTS" | tr ' ' '\n' | sort -u | tr '\n' ' ')
      echo "Found descendant processes: $ALL_DESCENDANTS"
    fi

    # Kill entire process tree - parent first
    kill "$PID" 2>/dev/null
    KILL_EXIT=$?

    # Also explicitly kill all descendants
    if [ -n "$ALL_DESCENDANTS" ]; then
      echo "$ALL_DESCENDANTS" | tr ' ' '\n' | xargs kill 2>/dev/null || true
    fi

    if [ "$KILL_EXIT" -eq 0 ]; then
      # Wait for all processes to actually die (up to 10 seconds)
      echo "Waiting for process tree to terminate..."
      for i in {1..20}; do
        # Check if parent is dead
        if ! kill -0 "$PID" 2>/dev/null; then
          # Also check if any descendants are still alive using recursive check
          REMAINING=$(get_descendants "$PID" | wc -w)
          if [ "$REMAINING" -eq 0 ]; then
            echo "Process $PID and entire process tree terminated successfully after ${i} attempts"
            KILLED_BY_PID=true
            break
          else
            echo "Still waiting... $REMAINING descendant(s) remain"
          fi
        fi
        sleep 0.5
      done

      if [ "$KILLED_BY_PID" = false ]; then
        echo "WARNING: Process tree did not terminate after 10 seconds, trying SIGKILL"
        # Force kill parent
        kill -9 "$PID" 2>/dev/null || true
        # Force kill any remaining descendants
        REMAINING_DESCENDANTS=$(get_descendants "$PID")
        if [ -n "$REMAINING_DESCENDANTS" ]; then
          echo "Force killing remaining descendants: $REMAINING_DESCENDANTS"
          echo "$REMAINING_DESCENDANTS" | tr ' ' '\n' | xargs kill -9 2>/dev/null || true
        fi
        sleep 1
        KILLED_BY_PID=true
      fi
    fi
  else
    echo "Process $PID is not running"
  fi
else
  echo "PID file $PID_FILE not found"
fi

# Only try pkill if we didn't successfully kill by PID
if [ "$KILLED_BY_PID" = false ]; then
  echo "Attempting pkill fallback..."
  # Kill by pattern as a fallback - run in completely isolated subshell
  PKILL_EXIT=1
  (
    set +e
    pkill -f "$CONFIG_PATTERN" 2>/dev/null
    exit $?
  ) && PKILL_EXIT=0 || PKILL_EXIT=$?

  if [ "$PKILL_EXIT" -eq 0 ]; then
    echo "Stopped additional processes matching pattern: $CONFIG_PATTERN"
  fi
fi

# Give processes time to clean up
sleep 1

echo "Backend stopped"
