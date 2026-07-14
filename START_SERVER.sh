#!/bin/bash

# Shop Billing Software - Final Production Start Script

echo "=================================================="
echo "🚀 Starting Shop Billing Software..."
echo "=================================================="
echo ""

# Navigate to project directory
cd /home/tejas/shop-billing-software

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Create temp directory if it doesn't exist
mkdir -p temp

# Start the Flask development server
echo "✅ Starting Flask server on http://127.0.0.1:5000"
echo ""
echo "Available Routes:"
echo "  📊 Dashboard: http://127.0.0.1:5000/"
echo "  📋 Invoices: http://127.0.0.1:5000/invoices"
echo "  📦 Products: http://127.0.0.1:5000/products"
echo "  👥 Customers: http://127.0.0.1:5000/customers"
echo "  📈 Reports: http://127.0.0.1:5000/reports"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m flask --app app run --host=127.0.0.1 --port=5000 --debug
