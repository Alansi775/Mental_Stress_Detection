#!/bin/bash
# Setup script - Run this ONCE to install everything

echo "======================================"
echo "🚀 Setting up GSR Stress Monitor"
echo "======================================"
echo ""

# Create virtual environment
echo "1️⃣ Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "2️⃣ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "3️⃣ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "4️⃣ Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Run: ./START.sh"
echo "  2. Open: http://localhost:8000/index.html"
echo "  3. Stop: ./STOP.sh"
echo ""
