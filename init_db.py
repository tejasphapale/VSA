#!/usr/bin/env python3
"""
Initialize the database with proper schema and sample data
Run this script once before starting the app
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, ShopInfo, Category, Product, Customer, Invoice, InvoiceItem, Payment
from app.utils import generate_invoice_number, generate_product_code, generate_customer_code

def init_database():
    """Initialize database with schema and sample data"""
    print("🔄 Initializing database...")
    
    app = create_app()
    
    with app.app_context():
        # Create all tables
        print("📋 Creating database tables...")
        db.create_all()
        print("✅ Tables created successfully")
        
        # Check if data already exists
        if ShopInfo.query.first():
            print("⚠️  Database already initialized with data. Skipping sample data...")
            return
        
        # Add Shop Info
        print("🏪 Adding shop information...")
        shop = ShopInfo(
            shop_name="VS ABRASIVE PRODUCTS",
            shop_email="vsabrasives@gmail.com",
            shop_phone="(02425) 297756",
            shop_mobile="+91-9876543210",
            shop_address="S.No. 206/1, B-1-R G Industrial Hub, Vehhale Road",
            shop_city="Sangamner",
            shop_state="Maharashtra",
            shop_zip="422605",
            gst_number="27AKLPG5978N1Z9",
            msme_number="UDYAM-MH-01-0202254",
            owner_name="Rajesh Kumar",
            bank_name="Union Bank of India",
            account_number="322501010033972",
            ifsc_code="UBIN0532258",
            bank_branch="Sangamner"
        )
        db.session.add(shop)
        db.session.commit()
        print("✅ Shop info added")
        
        # Add Category
        print("📁 Adding product category...")
        category = Category(
            name="Abrasive Products",
            description="Industrial abrasive materials for grinding and cutting"
        )
        db.session.add(category)
        db.session.commit()
        print("✅ Category added")
        
        # Add Products
        print("🏭 Adding products...")
        products_data = [
            ("Grinding Wheel", 150.00, 250.00, 100),
            ("Cutting Disc", 80.00, 180.00, 150),
            ("Sandpaper Sheets", 20.00, 60.00, 500),
            ("Polishing Pads", 100.00, 280.00, 80),
            ("Metal Oxide Belt", 200.00, 450.00, 50),
            ("Ceramic Grain", 120.00, 320.00, 120),
            ("Flap Disc", 90.00, 220.00, 100),
            ("Buffing Wheel", 110.00, 300.00, 75),
            ("Abrasive Cloth", 40.00, 120.00, 300),
            ("Wire Brush", 50.00, 150.00, 200),
            ("Diamond Blade", 500.00, 1200.00, 30),
        ]
        
        for idx, (name, purchase, selling, stock) in enumerate(products_data, 1):
            product = Product(
                product_code=generate_product_code(),
                product_name=name,
                description=f"{name} - Industrial grade",
                category_id=category.id,
                unit="Piece",
                purchase_price=Decimal(str(purchase)),
                selling_price=Decimal(str(selling)),
                quantity_in_stock=stock,
                reorder_level=20,
                hsn_code="6805",
                gst_percentage=Decimal("18"),
                is_active=True
            )
            db.session.add(product)
        
        db.session.commit()
        print(f"✅ Added 11 products")
        
        # Add Customers
        print("👥 Adding customers...")
        customers_data = [
            ("Amit Patel", "amit@example.com", "9876543210", "Mumbai", "Maharashtra", "27AKLPG5978N1Z9"),
            ("Rajesh Singh", "rajesh@example.com", "9876543211", "Delhi", "Delhi", "07ABCDE1234F1Z5"),
            ("Priya Sharma", "priya@example.com", "9876543212", "Bangalore", "Karnataka", "29ABCDE1234F1Z5"),
            ("Vikram Kumar", "vikram@example.com", "9876543213", "Pune", "Maharashtra", "27XYZPQ1234A1Z5"),
            ("Neha Desai", "neha@example.com", "9876543214", "Ahmedabad", "Gujarat", "24ABCDE1234F1Z5"),
        ]
        
        for name, email, phone, city, state, gst in customers_data:
            customer = Customer(
                customer_code=generate_customer_code(),
                customer_name=name,
                customer_email=email,
                customer_phone=phone,
                customer_address=f"{name}'s Address, {city}",
                customer_city=city,
                customer_state=state,
                gst_number=gst,
                credit_limit=Decimal("50000"),
                is_active=True
            )
            db.session.add(customer)
        
        db.session.commit()
        print(f"✅ Added 5 customers")
        
        print("\n" + "="*60)
        print("✅ DATABASE INITIALIZED SUCCESSFULLY!")
        print("="*60)
        print("\nDatabase ready with:")
        print("  ✓ Shop information")
        print("  ✓ Product category")
        print("  ✓ 11 Products")
        print("  ✓ 5 Customers")
        print("\n🚀 Ready to start the application!")
        print("="*60)

if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"\n❌ Error initializing database: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
