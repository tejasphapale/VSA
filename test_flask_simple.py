#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, '/home/tejas/shop-billing-software')
os.chdir('/home/tejas/shop-billing-software')

print("Loading app...")
from app import create_app

print("Creating app instance...")
app = create_app()

print(f"Total routes: {len(list(app.url_map.iter_rules()))}")

# List all routes
print("\nAll routes:")
for rule in app.url_map.iter_rules():
    if 'sales' in rule.rule:
        print(f"  ✓ {rule.rule} -> {rule.endpoint}")

# Test the API
print("\nTesting /api/sales/customers...")
with app.test_client() as client:
    resp = client.get('/api/sales/customers')
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.get_json()
        print(f"  Response: {len(data)} customers")
        if data:
            print(f"  First customer: {data[0]}")
    else:
        print(f"  Error: {resp.get_data(as_text=True)}")

print("\nDone!")
