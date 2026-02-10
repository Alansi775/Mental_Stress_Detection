#!/bin/bash
# STOP.sh - Stop all services

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}🛑 Stopping all services...${NC}"
echo ""

# Kill processes from pid files
if [ -f ".pids/flask.pid" ]; then
    FLASK_PID=$(cat .pids/flask.pid)
    kill $FLASK_PID 2>/dev/null && echo -e "${GREEN}✅ Flask stopped${NC}" || echo "Flask not running"
    rm .pids/flask.pid
fi

if [ -f ".pids/http.pid" ]; then
    HTTP_PID=$(cat .pids/http.pid)
    kill $HTTP_PID 2>/dev/null && echo -e "${GREEN}✅ HTTP server stopped${NC}" || echo "HTTP server not running"
    rm .pids/http.pid
fi

# Fallback: kill by port
echo "Cleaning up port 5001..."
lsof -ti:5001 | xargs kill -9 2>/dev/null || true

echo "Cleaning up port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

sleep 1

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
