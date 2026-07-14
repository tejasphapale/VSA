#!/bin/bash

# Shop Billing Software Startup Script
# This script sets up and runs the billing software

echo "=================================="
echo "Shop Billing Software"
echo "=================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

echo "✓ Python 3 found"
echo ""

# Navigate to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

# Create data directory if it doesn't exist
mkdir -p data

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting application..."
echo "📍 Open your browser and go to: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the application
python3 run.py
