#!/usr/bin/env python3
"""Test invoice creation fix"""
import sys
sys.path.insert(0, '/home/tejas/shop-billing-software')

from app import create_app, db
from app.models import Invoice, InvoiceItem, Product, Customer
from decimal import Decimal
from datetime import datetime

def test_invoice_creation():
    app = create_app()
    with app.app_context():
        # Get first customer and product
        customer = Customer.query.first()
        product = Product.query.first()
        
        if not customer or not product:
            print("ERROR: No customer or product found")
            return False
        
        # Test data
        qty = Decimal('5')
        up = Decimal('500')
        gst_p = Decimal('18')
        
        # Calculate values
        line_sub = qty * up  # 2500
        gst_amt = line_sub * gst_p / Decimal('100')  # 450
        cgst_p = gst_p / Decimal('2')  # 9
        sgst_p = gst_p / Decimal('2')  # 9
        cgst_amt = line_sub * cgst_p / Decimal('100')  # 225
        sgst_amt = line_sub * sgst_p / Decimal('100')  # 225
        line_tot = line_sub + gst_amt  # 2950
        
        print(f"Expected line_total: {line_tot}")
        
        # Create invoice
        invoice = Invoice(
            invoice_number=f'FIX-TEST-{datetime.now().timestamp()}',
            customer_id=customer.id,
            invoice_date=datetime.utcnow(),
            payment_method='Cash',
            status='Finalized',
            subtotal=line_sub,
            total_tax=gst_amt,
            discount=Decimal('0'),
            total_amount=line_tot
        )
        db.session.add(invoice)
        db.session.flush()
        
        # Create invoice item
        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=product.id,
            quantity=qty,
            unit_price=up,
            gst_percentage=gst_p,
            gst_amount=gst_amt,
            cgst_percentage=cgst_p,
            cgst_amount=cgst_amt,
            sgst_percentage=sgst_p,
            sgst_amount=sgst_amt,
            line_total=line_tot
        )
        db.session.add(invoice_item)
        
        try:
            db.session.commit()
            print(f"SUCCESS: Invoice {invoice.id} created")
            print(f"  Item line_total in DB: {invoice_item.line_total}")
            if invoice_item.line_total == line_tot:
                print("✓ line_total matches expected value!")
                return True
            else:
                print(f"✗ line_total mismatch: {invoice_item.line_total} != {line_tot}")
                return False
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    result = test_invoice_creation()
    sys.exit(0 if result else 1)
