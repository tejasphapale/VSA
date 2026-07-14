#!/usr/bin/env python3.10
import os
import sys

# Add project to path
sys.path.insert(0, '/home/tejas/shop-billing-software')
os.chdir('/home/tejas/shop-billing-software')

print("Starting Shop Billing Software...")
print("Importing Flask app...")

try:
    from app import create_app
    print("✓ App imported successfully")
    
    app = create_app()
    print("✓ App created successfully")
    
    print("Starting server on http://0.0.0.0:5000")
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
