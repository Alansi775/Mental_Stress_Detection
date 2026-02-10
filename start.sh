#!/bin/bash
# START.sh - Start everything with one command

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}======================================"
echo "🚀 Starting GSR Stress Monitor"
echo "======================================${NC}"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Run: ./setup.sh"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Create pid file directory
mkdir -p .pids

# Kill any existing processes on ports
echo "Cleaning up old processes..."
lsof -ti:5001 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2

# Start Flask backend
echo -e "${BLUE}1️⃣ Starting Flask backend on port 5001...${NC}"
python3 backend/onedrive_uploader.py > .pids/flask.log 2>&1 &
FLASK_PID=$!
echo $FLASK_PID > .pids/flask.pid
sleep 3

# Check if Flask started
if ! ps -p $FLASK_PID > /dev/null; then
    echo -e "${RED}❌ Flask failed to start. Check log:${NC}"
    cat .pids/flask.log
    exit 1
fi
echo -e "${GREEN}✅ Flask running (PID: $FLASK_PID)${NC}"

# Start HTTP server for UI
echo -e "${BLUE}2️⃣ Starting HTTP server on port 8000...${NC}"
cd ui
python3 -m http.server 8000 > ../.pids/http.log 2>&1 &
HTTP_PID=$!
echo $HTTP_PID > ../.pids/http.pid
cd ..
sleep 2

# Check if HTTP server started
if ! ps -p $HTTP_PID > /dev/null; then
    echo -e "${RED}❌ HTTP server failed to start. Check log:${NC}"
    cat .pids/http.log
    kill $FLASK_PID 2>/dev/null
    exit 1
fi
echo -e "${GREEN}✅ HTTP server running (PID: $HTTP_PID)${NC}"

echo ""
echo -e "${GREEN}======================================"
echo "✅ All systems running!"
echo "======================================${NC}"
echo ""
echo "Access the UI at:"
echo -e "${BLUE}  http://localhost:8000/index.html${NC}"
echo ""
echo "Backend API at:"
echo -e "${BLUE}  http://localhost:5001/api/upload${NC}"
echo ""
echo "To stop everything, run: ./STOP.sh"
echo ""

# Keep script running to show logs
echo -e "${BLUE}Watching logs (Ctrl+C to view, use ./STOP.sh to stop):${NC}"
tail -f .pids/flask.log
