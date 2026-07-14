from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from decimal import Decimal

db = SQLAlchemy()

class ShopInfo(db.Model):
    """Store shop information"""
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), nullable=False)
    shop_email = db.Column(db.String(100))
    shop_phone = db.Column(db.String(20))
    shop_mobile = db.Column(db.String(20))
    shop_address = db.Column(db.String(255))
    shop_city = db.Column(db.String(100))
    shop_state = db.Column(db.String(100))
    shop_zip = db.Column(db.String(10))
    gst_number = db.Column(db.String(50))
    msme_number = db.Column(db.String(50))
    owner_name = db.Column(db.String(100))
    bank_name = db.Column(db.String(100))
    account_number = db.Column(db.String(50))
    ifsc_code = db.Column(db.String(20))
    bank_branch = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'shop_name': self.shop_name,
            'shop_email': self.shop_email,
            'shop_phone': self.shop_phone,
            'shop_mobile': self.shop_mobile,
            'shop_address': self.shop_address,
            'shop_city': self.shop_city,
            'shop_state': self.shop_state,
            'shop_zip': self.shop_zip,
            'gst_number': self.gst_number,
            'msme_number': self.msme_number,
            'owner_name': self.owner_name,
            'bank_name': self.bank_name,
            'account_number': self.account_number,
            'ifsc_code': self.ifsc_code,
            'bank_branch': self.bank_branch
        }


class Category(db.Model):
    """Product categories"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship('Product', backref='category', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'product_count': len(self.products)
        }


class Product(db.Model):
    """Shop products"""
    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(50), nullable=False, unique=True)
    product_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)  # Made optional
    unit = db.Column(db.String(20), default='Piece')  # Piece, kg, liter, etc.
    purchase_price = db.Column(db.Numeric(10, 2), nullable=False)
    selling_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity_in_stock = db.Column(db.Integer, default=0)
    reorder_level = db.Column(db.Integer, default=10)
    gst_percentage = db.Column(db.Numeric(5, 2), default=0)
    cgst_percentage = db.Column(db.Numeric(5, 2), default=0)  # CGST percentage
    sgst_percentage = db.Column(db.Numeric(5, 2), default=0)  # SGST percentage
    hsn_code = db.Column(db.String(50), default='68042210')  # HSN/SAC code for abrasive wheels
    image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    invoice_items = db.relationship('InvoiceItem', backref='product', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else '',
            'unit': self.unit,
            'purchase_price': float(self.purchase_price),
            'selling_price': float(self.selling_price),
            'quantity_in_stock': self.quantity_in_stock,
            'reorder_level': self.reorder_level,
            'gst_percentage': float(self.gst_percentage),
            'cgst_percentage': float(self.cgst_percentage),
            'sgst_percentage': float(self.sgst_percentage),
            'hsn_code': self.hsn_code,
            'is_active': self.is_active
        }


class Customer(db.Model):
    """Customer information"""
    id = db.Column(db.Integer, primary_key=True)
    customer_code = db.Column(db.String(50), nullable=False, unique=True)
    customer_name = db.Column(db.String(150), nullable=False)
    customer_phone = db.Column(db.String(20))
    customer_email = db.Column(db.String(100))
    customer_address = db.Column(db.String(255))
    customer_city = db.Column(db.String(100))
    customer_state = db.Column(db.String(100))
    gst_number = db.Column(db.String(50))
    credit_limit = db.Column(db.Numeric(12, 2), default=0)
    opening_balance = db.Column(db.Numeric(12, 2), default=0)  # Money owed or balance
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    invoices = db.relationship('Invoice', backref='customer', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'customer_code': self.customer_code,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_email': self.customer_email,
            'customer_address': self.customer_address,
            'customer_city': self.customer_city,
            'customer_state': self.customer_state,
            'gst_number': self.gst_number,
            'credit_limit': float(self.credit_limit),
            'opening_balance': float(self.opening_balance),
            'is_active': self.is_active
        }


class Invoice(db.Model):
    """Sales invoices"""
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), nullable=False, unique=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    invoice_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    total_tax = db.Column(db.Numeric(12, 2), default=0)
    discount = db.Column(db.Numeric(12, 2), default=0)
    transport_charges = db.Column(db.Numeric(12, 2), default=0)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    payment_method = db.Column(db.String(50))  # Cash, Card, Cheque, UPI, Credit
    payment_status = db.Column(db.String(20), default='Unpaid')  # Paid, Unpaid, Partial
    status = db.Column(db.String(20), default='Draft')  # Draft, Finalized, Cancelled
    notes = db.Column(db.String(500))
    
    # Additional invoice fields
    po_number = db.Column(db.String(100))  # Purchase Order Number
    date_of_supply = db.Column(db.DateTime)
    place_of_supply = db.Column(db.String(100))  # Sangamner
    state = db.Column(db.String(100))  # Maharashtra
    challan_no = db.Column(db.String(100))
    transport_mode = db.Column(db.String(100))  # BY ROAD
    vehicle_number = db.Column(db.String(50))
    e_weighment = db.Column(db.String(100))
    pay_terms = db.Column(db.String(50))  # 0 Days
    contact_person = db.Column(db.String(100))
    shop_gst = db.Column(db.String(50))
    shop_pan = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('InvoiceItem', backref='invoice', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='invoice', lazy=True, cascade='all, delete-orphan')

    def to_dict(self, with_items=False):
        data = {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'customer_id': self.customer_id,
            'customer_name': self.customer.customer_name if self.customer else 'Walk-in Customer',
            'invoice_date': self.invoice_date.strftime('%Y-%m-%d'),
            'due_date': self.due_date.strftime('%Y-%m-%d') if self.due_date else None,
            'subtotal': float(self.subtotal),
            'total_tax': float(self.total_tax),
            'discount': float(self.discount),
            'transport_charges': float(self.transport_charges) if self.transport_charges else 0,
            'total_amount': float(self.total_amount),
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'status': self.status,
            'notes': self.notes
        }
        if with_items:
            data['items'] = [item.to_dict() for item in self.items]
        return data


class InvoiceItem(db.Model):
    """Line items in invoices"""
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    gst_percentage = db.Column(db.Numeric(5, 2), default=0)
    cgst_percentage = db.Column(db.Numeric(5, 2), default=0)  # CGST percentage
    sgst_percentage = db.Column(db.Numeric(5, 2), default=0)  # SGST percentage
    gst_amount = db.Column(db.Numeric(10, 2), default=0)
    cgst_amount = db.Column(db.Numeric(10, 2), default=0)  # CGST amount
    sgst_amount = db.Column(db.Numeric(10, 2), default=0)  # SGST amount
    line_total = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.product_name if self.product else '',
            'quantity': float(self.quantity),
            'unit': self.product.unit if self.product else '',
            'unit_price': float(self.unit_price),
            'gst_percentage': float(self.gst_percentage),
            'cgst_percentage': float(self.cgst_percentage),
            'sgst_percentage': float(self.sgst_percentage),
            'gst_amount': float(self.gst_amount),
            'cgst_amount': float(self.cgst_amount),
            'sgst_amount': float(self.sgst_amount),
            'line_total': float(self.line_total)
        }


class Payment(db.Model):
    """Payment records"""
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_method = db.Column(db.String(50))  # Cash, Card, Cheque, UPI
    reference_number = db.Column(db.String(100))
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'payment_date': self.payment_date.strftime('%Y-%m-%d'),
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'reference_number': self.reference_number,
            'notes': self.notes
        }


class Expense(db.Model):
    """Shop expenses"""
    id = db.Column(db.Integer, primary_key=True)
    expense_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    category = db.Column(db.String(100), nullable=False)  # Rent, Electricity, etc.
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255))
    payment_method = db.Column(db.String(50))
    reference_number = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'expense_date': self.expense_date.strftime('%Y-%m-%d'),
            'category': self.category,
            'amount': float(self.amount),
            'description': self.description,
            'payment_method': self.payment_method,
            'reference_number': self.reference_number
        }
