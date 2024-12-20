#!/bin/bash
set -e

# Forward signals to child processes
trap 'kill -TERM $PID' TERM INT

# Start the main process
exec "$@" &
PID=$!
wait $PID
