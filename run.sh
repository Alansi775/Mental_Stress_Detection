#!/bin/bash

# Quick start script for GSR Stress Monitor
# شغيل سريع - كل الأشياء معاً

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
VENV_PIP="$PROJECT_DIR/.venv/bin/pip"

echo " GSR Stress Monitor - Starting..."
echo ""

# Check if venv exists
if [ ! -d "$PROJECT_DIR/.venv" ]; then
  echo "❌ Virtual environment not found at .venv"
  echo "   Create it first: python3 -m venv .venv"
  exit 1
fi

# Verify Python
if ! $VENV_PYTHON --version > /dev/null 2>&1; then
  echo "❌ Python not found in venv"
  exit 1
fi

echo " Python venv found"
echo ""

# Install/update dependencies
echo " Checking dependencies..."
$VENV_PIP install -q flask flask-cors requests python-dotenv

echo " Dependencies ready"
echo ""

# Show instructions
echo "========== SETUP INSTRUCTIONS =========="
echo ""
echo "Terminal 1: ESP32 Monitor"
echo "   pio device monitor --port /dev/cu.usbserial-0001 -b 115200"
echo ""
echo "Terminal 2: Web Server + Backend (run this script)"
echo ""
echo "Then open browser:"
echo "   http://localhost:8000/index.html"
echo ""
echo "=========================================="
echo ""

# Kill any existing processes on these ports
kill_port() {
  lsof -i ":$1" | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null || true
}

echo "🧹 Cleaning up old processes..."
kill_port 8000
kill_port 5000
sleep 1

echo ""
echo " Starting services..."
echo ""

# Start web server in background
echo "Starting Web Server (port 8000)..."
cd "$PROJECT_DIR/ui"
python3 -m http.server 8000 > /tmp/web_server.log 2>&1 &
WEB_PID=$!
echo "   ✓ PID: $WEB_PID"

sleep 1

# Start Python backend in foreground
echo "Starting OneDrive Backend (port 5000)..."
cd "$PROJECT_DIR/backend"
$VENV_PYTHON onedrive_upload.py

# Cleanup on exit
echo ""
echo "Shutting down..."
kill $WEB_PID 2>/dev/null || true
echo "✓ All services stopped"
