#!/usr/bin/env python3
"""Final test to verify invoice creation with proper CGST/SGST"""
import sys
sys.path.insert(0, '/home/tejas/shop-billing-software')

from app import create_app, db
from app.models import Invoice, InvoiceItem, Product, Customer
from decimal import Decimal
from datetime import datetime
import json

def test():
    print("=" * 60)
    print("FINAL INVOICE CREATION TEST")
    print("=" * 60)
    
    app = create_app()
    with app.app_context():
        # Get sample customer and product
        customer = Customer.query.first()
        product = Product.query.first()
        
        if not customer:
            print("❌ No customer found")
            return False
        
        if not product:
            print("❌ No product found")
            return False
        
        print(f"\n✓ Customer: {customer.customer_name}")
        print(f"✓ Product: {product.product_name}")
        print(f"✓ Product GST: {product.gst_percentage}%")
        print(f"✓ Product Price: {product.selling_price}")
        
        # Simulate form data
        form_data = {
            "customer_id": customer.id,
            "invoice_date": "2026-06-03",
            "payment_method": "Card",
            "items": [{
                "product_id": product.id,
                "quantity": 5,
                "unit_price": 500,
                "gst_percentage": 18  # FROM FORM OR PRODUCT
            }]
        }
        
        print(f"\n📥 Input Data:")
        print(f"   Quantity: {form_data['items'][0]['quantity']}")
        print(f"   Unit Price: {form_data['items'][0]['unit_price']}")
        print(f"   GST%: {form_data['items'][0]['gst_percentage']}")
        
        # Create invoice manually (simulating backend)
        try:
            print(f"\n⚙️  Creating invoice...")
            
            invoice = Invoice(
                invoice_number=f"TEST-{datetime.now().timestamp()}",
                customer_id=form_data['customer_id'],
                invoice_date=datetime.strptime(form_data['invoice_date'], '%Y-%m-%d'),
                payment_method=form_data['payment_method'],
                status='Finalized'
            )
            db.session.add(invoice)
            db.session.flush()
            
            # Process item
            item_data = form_data['items'][0]
            prod = Product.query.get(item_data['product_id'])
            
            item_qty = Decimal(str(item_data.get('quantity') or 1))
            item_price = Decimal(str(item_data.get('unit_price') or prod.selling_price or 0))
            item_gst = Decimal(str(item_data.get('gst_percentage') or prod.gst_percentage or 0))
            
            # Ensure GST is not zero
            if item_gst == 0 and prod.gst_percentage and prod.gst_percentage > 0:
                item_gst = Decimal(str(prod.gst_percentage))
            
            item_line_subtotal = item_qty * item_price  # 2500
            item_total_gst = item_line_subtotal * item_gst / Decimal('100')  # 450
            item_cgst_perc = item_gst / Decimal('2')  # 9
            item_sgst_perc = item_gst / Decimal('2')  # 9
            item_cgst_amt = item_line_subtotal * item_cgst_perc / Decimal('100')  # 225
            item_sgst_amt = item_line_subtotal * item_sgst_perc / Decimal('100')  # 225
            item_line_total = item_line_subtotal + item_total_gst  # 2950
            
            print(f"\n📊 Calculations:")
            print(f"   Line Subtotal: {item_line_subtotal}")
            print(f"   GST Amount (18%): {item_total_gst}")
            print(f"   CGST%: {item_cgst_perc}%")
            print(f"   SGST%: {item_sgst_perc}%")
            print(f"   CGST Amount: {item_cgst_amt}")
            print(f"   SGST Amount: {item_sgst_amt}")
            print(f"   Line Total: {item_line_total}")
            
            new_item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=item_data['product_id'],
                quantity=item_qty,
                unit_price=item_price,
                gst_percentage=item_gst,
                gst_amount=item_total_gst,
                cgst_percentage=item_cgst_perc,
                cgst_amount=item_cgst_amt,
                sgst_percentage=item_sgst_perc,
                sgst_amount=item_sgst_amt,
                line_total=item_line_total
            )
            
            print(f"\n✓ Item object created")
            print(f"   line_total = {new_item.line_total}")
            
            db.session.add(new_item)
            invoice.subtotal = item_line_subtotal
            invoice.total_tax = item_total_gst
            invoice.discount = Decimal('0')
            invoice.total_amount = item_line_subtotal + item_total_gst
            
            db.session.commit()
            
            print(f"\n✅ Invoice saved to database!")
            print(f"   Invoice ID: {invoice.id}")
            print(f"   Invoice Number: {invoice.invoice_number}")
            print(f"   Item line_total in DB: {new_item.line_total}")
            
            # Verify
            saved_invoice = Invoice.query.get(invoice.id)
            saved_item = InvoiceItem.query.filter_by(invoice_id=invoice.id).first()
            
            if saved_item.line_total is not None:
                print(f"\n✅ SUCCESS! line_total is NOT None: {saved_item.line_total}")
                if float(saved_item.line_total) == float(item_line_total):
                    print(f"✅ line_total value is CORRECT: {saved_item.line_total}")
                    return True
                else:
                    print(f"❌ line_total mismatch: {saved_item.line_total} != {item_line_total}")
                    return False
            else:
                print(f"\n❌ FAILED! line_total is None")
                return False
                
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test()
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ TEST FAILED")
    print("=" * 60)
    sys.exit(0 if success else 1)
