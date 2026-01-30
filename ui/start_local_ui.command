#!/bin/bash
# Double-click this file to start the local UI server and open Chrome
# It will run a simple Python HTTP server serving files from this folder.

cd "$(dirname "$0")"

# Check for python3
if ! command -v python3 >/dev/null 2>&1; then
  osascript -e 'display alert "Python3 not found" message "Please install Python 3 to run the local UI."'
  exit 1
fi

# Start server in background and keep terminal open
python3 -m http.server 8000 --bind 127.0.0.1 >/tmp/gsr_ui_server.log 2>&1 &
SERVER_PID=$!
sleep 0.5

# Open Chrome to the local UI page
open -a "Google Chrome" "http://localhost:8000/index.html"

echo "Local UI server running at http://localhost:8000/index.html (pid $SERVER_PID)"
echo "Log: /tmp/gsr_ui_server.log"
echo "Press Ctrl+C in this Terminal window to stop the server." 

# Wait for the background server process so the Terminal window stays open
wait $SERVER_PID
