#!/bin/bash

# Test all connections before running

echo "🧪 Testing GSR System..."
echo ""

# Test venv
VENV="/Users/mackbook/Projects/Mental_Stress_Detection/.venv/bin/python"
if $VENV --version > /dev/null 2>&1; then
  echo "✅ Python venv: OK"
else
  echo "❌ Python venv: FAILED"
  exit 1
fi

# Test packages
if $VENV -c "import flask, requests, dotenv" 2>/dev/null; then
  echo "✅ Python packages: OK"
else
  echo "❌ Python packages: MISSING - run: /Users/mackbook/Projects/Mental_Stress_Detection/.venv/bin/pip install -r backend/requirements.txt"
  exit 1
fi

# Test ESP32 port
if ls /dev/cu.usbserial* > /dev/null 2>&1; then
  echo "✅ ESP32 port: OK"
  ls -la /dev/cu.usbserial*
else
  echo "⚠️  ESP32 port: NOT FOUND - Connect USB cable"
fi

echo ""
echo "🚀 Ready to start!"
echo ""
echo "Run: ./run.sh"
