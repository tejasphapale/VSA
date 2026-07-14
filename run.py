#!/usr/bin/env python3
import os
import sys

# Set the correct paths for Flask
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

os.chdir(base_dir)

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
