"""Utility script to replace current products with a clean set supplied by the user.

Usage (run once from project root, inside virtualenv):
    source .venv/bin/activate
    python3 update_products.py

What it does:
- Dumps current products to temp/products_backup_<ts>.json
- Deletes all products from the database
- Inserts the new product list (HSN = 68042210) with sensible defaults
- Prints a short summary

This is non-interactive but creates a JSON backup so you can restore if needed.
"""

import os
import json
from datetime import datetime

from app import create_app
from app.models import db, Product
from app.utils import generate_product_code

NEW_PRODUCTS = [
    "150x80X25 H",
    "150x80X25 S",
    "150x78X25 H",
    "150x78X25 P-20",
    "150x80x16 485",
    "150*80*16 S",
    "150*80*16 M",
    "150*80*16 SS",
    "203*103/84*38.1 M",
    "150*118/80*44.5 TR3",
    "203*103/84*38.1 MI",
]

HSN = "68042210"
DEFAULT_GST = 18.0
DEFAULT_UNIT = "NOS"
DEFAULT_PRICE = 0.0

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        temp_dir = os.path.join(project_root, 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        # Backup existing products
        products = Product.query.all()
        backup = []
        for p in products:
            backup.append({
                'id': p.id,
                'product_code': getattr(p, 'product_code', None),
                'product_name': p.product_name,
                'hsn_code': p.hsn_code,
                'selling_price': float(p.selling_price or 0),
                'gst_percentage': float(p.gst_percentage or 0),
                'unit': getattr(p, 'unit', None),
                'quantity_in_stock': float(getattr(p, 'quantity_in_stock', 0) or 0),
                'is_active': bool(getattr(p, 'is_active', True))
            })

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(temp_dir, f'products_backup_{ts}.json')
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup, f, indent=2, ensure_ascii=False)

        print(f'Backed up {len(backup)} products to {backup_file}')

        # Delete all existing products
        try:
            deleted = db.session.query(Product).delete()
            db.session.commit()
            print(f'Deleted {deleted} existing products')
        except Exception as e:
            db.session.rollback()
            print('Failed to delete existing products:', e)
            raise

        # Insert new products
        created = 0
        for name in NEW_PRODUCTS:
            try:
                code = generate_product_code(name)
            except Exception:
                code = f'PRD-{datetime.now().strftime("%Y%m%d%H%M%S")}-{created}'
            p = Product(
                product_code=code,
                product_name=name,
                hsn_code=HSN,
                purchase_price=DEFAULT_PRICE,
                selling_price=DEFAULT_PRICE,
                gst_percentage=DEFAULT_GST,
                unit=DEFAULT_UNIT,
                quantity_in_stock=0,
                is_active=True
            )
            db.session.add(p)
            created += 1

        try:
            db.session.commit()
            print(f'Created {created} new products with HSN {HSN}')
        except Exception as e:
            db.session.rollback()
            print('Failed to insert new products:', e)
            raise

        print('Done. Verify in product list or run the app and create an invoice to see HSN printed on invoice.')
