#!/bin/bash

# FINAL WORKING STARTUP SCRIPT
cd /home/tejas/shop-billing-software

# Clear everything
rm -rf __pycache__ app/__pycache__ 2>/dev/null

# Activate venv
source .venv/bin/activate

# Start Flask server - FINAL VERSION
export FLASK_APP=run.py
export FLASK_ENV=production
export PYTHONUNBUFFERED=1

# Run the server
exec python3.10 run.py
