#!/usr/bin/env python3
import os
import sys

# Set the correct paths for Flask
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)
os.chdir(base_dir)

print("Starting app initialization...")
try:
    from app import create_app
    print("✓ App module imported")
    
    app = create_app()
    print("✓ App created")
    
    print("\nStarting Flask server on 0.0.0.0:5000...")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
