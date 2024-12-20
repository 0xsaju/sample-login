#!/bin/bash
set -e

# Forward SIGTERM to the child processes
trap 'kill -TERM $PID' TERM INT

# Add execute permissions to docker-entrypoint.sh
chmod +x docker-entrypoint.sh

# Start the main process
exec "$@" &
PID=$!

# Wait for process to end
wait $PID
trap - TERM INT
wait $PID
EXIT_STATUS=$?
