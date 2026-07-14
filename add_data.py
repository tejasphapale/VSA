#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/tejas/shop-billing-software')

from app import create_app
from app.models import db, Product, Customer
from decimal import Decimal

app = create_app()

with app.app_context():
    # Products to add
    products_data = [
        {'name': '150x80X25 H', 'code': 'PROD-150-80-25-H', 'gst': 18},
        {'name': '150x80X25 S', 'code': 'PROD-150-80-25-S', 'gst': 18},
        {'name': '150x78X25 H', 'code': 'PROD-150-78-25-H', 'gst': 18},
        {'name': '150x78X25 P-20', 'code': 'PROD-150-78-25-P20', 'gst': 18},
        {'name': '150x80x16 485', 'code': 'PROD-150-80-16-485', 'gst': 18},
        {'name': '150*80*16 S', 'code': 'PROD-150-80-16-S', 'gst': 18},
        {'name': '150*80*16 M', 'code': 'PROD-150-80-16-M', 'gst': 18},
        {'name': '150*80*16 SS', 'code': 'PROD-150-80-16-SS', 'gst': 18},
        {'name': '203*103/84*38.1 M', 'code': 'PROD-203-103-84-M', 'gst': 18},
        {'name': '150*118/80*44.5 TR3', 'code': 'PROD-150-118-80-TR3', 'gst': 18},
        {'name': '203*103/84*38.1 MI', 'code': 'PROD-203-103-84-MI', 'gst': 18},
    ]
    
    # Customers to add
    customers_data = [
        {
            'name': 'Sandip Mama',
            'phone': '9999999999',
            'email': 'sandip@example.com',
            'address': 'Mumbai, Maharashtra',
            'city': 'Mumbai',
            'state': 'Maharashtra'
        },
        {
            'name': 'Rajesh Kumar',
            'phone': '9876543210',
            'email': 'rajesh@example.com',
            'address': 'Delhi',
            'city': 'Delhi',
            'state': 'Delhi'
        },
        {
            'name': 'Priya Singh',
            'phone': '9123456789',
            'email': 'priya@example.com',
            'address': 'Bangalore, Karnataka',
            'city': 'Bangalore',
            'state': 'Karnataka'
        },
        {
            'name': 'Amit Patel',
            'phone': '8765432109',
            'email': 'amit@example.com',
            'address': 'Ahmedabad, Gujarat',
            'city': 'Ahmedabad',
            'state': 'Gujarat'
        },
        {
            'name': 'Neha Gupta',
            'phone': '7654321098',
            'email': 'neha@example.com',
            'address': 'Hyderabad, Telangana',
            'city': 'Hyderabad',
            'state': 'Telangana'
        },
    ]
    
    print("Adding products...")
    for i, prod_data in enumerate(products_data):
        # Check if product already exists
        existing = Product.query.filter_by(product_code=prod_data['code']).first()
        if not existing:
            product = Product(
                product_code=prod_data['code'],
                product_name=prod_data['name'],
                selling_price=Decimal('500.00'),
                purchase_price=Decimal('400.00'),
                gst_percentage=prod_data['gst'],
                quantity_in_stock=100,
                reorder_level=10,
                is_active=True
            )
            db.session.add(product)
            print(f"  ✓ Added: {prod_data['name']}")
        else:
            print(f"  ⚠ Already exists: {prod_data['name']}")
    
    print("\nAdding customers...")
    for i, cust_data in enumerate(customers_data):
        # Check if customer already exists
        existing = Customer.query.filter_by(customer_phone=cust_data['phone']).first()
        if not existing:
            customer = Customer(
                customer_code=f'CUST-{i+1:05d}',
                customer_name=cust_data['name'],
                customer_phone=cust_data['phone'],
                customer_email=cust_data['email'],
                customer_address=cust_data['address'],
                customer_city=cust_data['city'],
                customer_state=cust_data['state'],
                gst_number='',
                is_active=True
            )
            db.session.add(customer)
            print(f"  ✓ Added: {cust_data['name']}")
        else:
            print(f"  ⚠ Already exists: {cust_data['name']}")
    
    db.session.commit()
    print("\n✅ All products and customers added successfully!")
