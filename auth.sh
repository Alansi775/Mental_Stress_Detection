#!/bin/bash
# Quick OneDrive Authentication Setup

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}======================================"
echo "🔐 OneDrive Authentication Setup"
echo "======================================${NC}"
echo ""
echo "This will authenticate your OneDrive account"
echo "using your work/school account."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Run: ./setup.sh"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Run simplified Device Code authentication
echo "Starting OneDrive authentication..."
echo ""
python3 backend/simple_auth.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Authentication complete!${NC}"
    echo "Ready to use the system with: ./START.sh"
else
    echo ""
    echo -e "${RED}❌ Authentication failed${NC}"
    exit 1
fi
