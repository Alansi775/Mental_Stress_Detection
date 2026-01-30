Double-click start_local_ui.command (macOS)

1) Make the script executable (one-time). In a Terminal, run:

   chmod +x /Users/mackbook/Projects/GSR_ESP32/ui/start_local_ui.command

2) Double-click `start_local_ui.command` in Finder. A Terminal window will open and start the local server.

3) The script will automatically open Google Chrome at:

   http://localhost:8000/index.html

Notes:
- Your computer must be connected to the ESP32 AP (GSR_Monitor) for the page to fetch data from http://192.168.4.1.
- The server log is at /tmp/gsr_ui_server.log.
- Press Ctrl+C in the Terminal window to stop the server.

If you want me to create a native macOS .app (Automator) that does this without running Terminal, I can add that next.