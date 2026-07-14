#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/tejas/shop-billing-software')

from app import create_app
from app.models import db, Product

app = create_app()

with app.app_context():
    # Get all products and set is_active to True
    products = Product.query.all()
    
    print(f"Found {len(products)} products")
    for product in products:
        if not product.is_active:
            product.is_active = True
            print(f"  ✓ Activated: {product.product_name}")
    
    db.session.commit()
    print("\n✅ All products activated!")
    
    # Show all active products
    active_products = Product.query.filter_by(is_active=True).all()
    print(f"\n📦 Total active products: {len(active_products)}")
    for prod in active_products:
        print(f"  - {prod.product_name} ({prod.product_code})")
