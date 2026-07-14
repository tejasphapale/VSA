from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
from datetime import datetime, timedelta
from decimal import Decimal
import os
from functools import wraps
from app.models import db, ShopInfo, Category, Product, Customer, Invoice, InvoiceItem, Payment, Expense
from app.utils import generate_invoice_number, generate_product_code, generate_customer_code, amount_in_words
from sqlalchemy import func
import json
from urllib.parse import quote
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def create_app():
    # Get the absolute path to the project root
    basedir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.dirname(basedir)
    
    app = Flask(__name__, 
                template_folder=os.path.join(project_root, 'templates'),
                static_folder=os.path.join(project_root, 'static'))
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(project_root, "data", "billing.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    app.config['SECRET_KEY'] = 'vsa-secret-key-change-in-production'
    app.config['SESSION_PERMANENT'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    # Register Jinja2 globals
    app.jinja_env.globals.update(amount_in_words=amount_in_words)
    
    # Login required decorator
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                return redirect('/login')
            return f(*args, **kwargs)
        return decorated_function
    
    # ==================== LOGIN ====================
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            app.logger.info(f"Login attempt - Username: {username}, Password: {password}")
            
            if username == 'vsa' and password == 'vsa@123':
                session['logged_in'] = True
                session['username'] = username
                session.permanent = False
                app.logger.info(f"Login successful for {username}, session: {session}")
                return redirect('/')
            else:
                app.logger.info(f"Login failed for {username}")
                return render_template('login.html', error=True)
        
        return render_template('login.html', error=False)
    
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect('/login')
    
    # ==================== DASHBOARD ====================
    @app.route('/')
    @login_required
    def dashboard():
        today = datetime.utcnow().date()
        start_of_month = datetime(today.year, today.month, 1).date()
        
        today_sales = db.session.query(func.sum(Invoice.total_amount)).filter(
            db.func.date(Invoice.invoice_date) == today,
            Invoice.status == 'Finalized'
        ).scalar() or 0
        
        month_sales = db.session.query(func.sum(Invoice.total_amount)).filter(
            db.func.date(Invoice.invoice_date) >= start_of_month,
            Invoice.status == 'Finalized'
        ).scalar() or 0
        
        total_products = Product.query.count()
        total_customers = Customer.query.count()
        pending_invoices = Invoice.query.filter_by(payment_status='Unpaid', status='Finalized').count()
        low_stock = Product.query.filter(Product.quantity_in_stock <= Product.reorder_level).count()
        
        recent_invoices = Invoice.query.filter_by(status='Finalized').order_by(Invoice.invoice_date.desc()).limit(10).all()
        
        stats = {
            'today_sales': float(today_sales),
            'month_sales': float(month_sales),
            'total_products': total_products,
            'total_customers': total_customers,
            'pending_invoices': pending_invoices,
            'low_stock': low_stock
        }
        
        return render_template('dashboard.html', stats=stats, recent_invoices=recent_invoices)
    
    # ==================== SHOP SETTINGS ====================
    @app.route('/api/shop-info', methods=['GET', 'POST', 'PUT'])
    def shop_info():
        shop = ShopInfo.query.first()
        
        if request.method == 'GET':
            if not shop:
                return jsonify({'error': 'Shop info not found'}), 404
            return jsonify(shop.to_dict())
        
        elif request.method == 'POST':
            if shop:
                return jsonify({'error': 'Shop info already exists. Use PUT to update.'}), 400
            
            data = request.get_json()
            shop = ShopInfo(
                shop_name=data.get('shop_name'),
                shop_email=data.get('shop_email'),
                shop_phone=data.get('shop_phone'),
                shop_mobile=data.get('shop_mobile'),
                shop_address=data.get('shop_address'),
                shop_city=data.get('shop_city'),
                shop_state=data.get('shop_state'),
                shop_zip=data.get('shop_zip'),
                gst_number=data.get('gst_number'),
                msme_number=data.get('msme_number'),
                owner_name=data.get('owner_name'),
                bank_name=data.get('bank_name'),
                account_number=data.get('account_number'),
                ifsc_code=data.get('ifsc_code'),
                bank_branch=data.get('bank_branch')
            )
            db.session.add(shop)
            db.session.commit()
            return jsonify(shop.to_dict()), 201
        
        elif request.method == 'PUT':
            if not shop:
                return jsonify({'error': 'Shop info not found'}), 404
            
            data = request.get_json()
            shop.shop_name = data.get('shop_name', shop.shop_name)
            shop.shop_email = data.get('shop_email', shop.shop_email)
            shop.shop_phone = data.get('shop_phone', shop.shop_phone)
            shop.shop_mobile = data.get('shop_mobile', shop.shop_mobile)
            shop.shop_address = data.get('shop_address', shop.shop_address)
            shop.shop_city = data.get('shop_city', shop.shop_city)
            shop.shop_state = data.get('shop_state', shop.shop_state)
            shop.shop_zip = data.get('shop_zip', shop.shop_zip)
            shop.gst_number = data.get('gst_number', shop.gst_number)
            shop.msme_number = data.get('msme_number', shop.msme_number)
            shop.owner_name = data.get('owner_name', shop.owner_name)
            shop.bank_name = data.get('bank_name', shop.bank_name)
            shop.account_number = data.get('account_number', shop.account_number)
            shop.ifsc_code = data.get('ifsc_code', shop.ifsc_code)
            shop.bank_branch = data.get('bank_branch', shop.bank_branch)
            db.session.commit()
            return jsonify(shop.to_dict())
    
    # ==================== CATEGORIES ====================
    @app.route('/api/categories', methods=['GET', 'POST'])
    def categories():
        if request.method == 'GET':
            categories = Category.query.all()
            return jsonify([cat.to_dict() for cat in categories])
        
        elif request.method == 'POST':
            data = request.get_json()
            category = Category(
                name=data.get('name'),
                description=data.get('description', '')
            )
            db.session.add(category)
            db.session.commit()
            return jsonify(category.to_dict()), 201
    
    @app.route('/api/categories/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    def category_detail(id):
        category = Category.query.get_or_404(id)
        
        if request.method == 'GET':
            return jsonify(category.to_dict())
        
        elif request.method == 'PUT':
            data = request.get_json()
            category.name = data.get('name', category.name)
            category.description = data.get('description', category.description)
            db.session.commit()
            return jsonify(category.to_dict())
        
        elif request.method == 'DELETE':
            db.session.delete(category)
            db.session.commit()
            return '', 204
    
    # ==================== PRODUCTS ====================
    @app.route('/api/products', methods=['GET', 'POST'])
    def products():
        if request.method == 'GET':
            products = Product.query.filter_by(is_active=True).all()
            return jsonify([prod.to_dict() for prod in products])
        
        elif request.method == 'POST':
            data = request.get_json()
            product = Product(
                product_code=generate_product_code(),
                product_name=data.get('product_name'),
                description=data.get('description', ''),
                category_id=data.get('category_id'),
                unit=data.get('unit', 'Piece'),
                purchase_price=Decimal(str(data.get('purchase_price', 0))),
                selling_price=Decimal(str(data.get('selling_price', 0))),
                quantity_in_stock=data.get('quantity_in_stock', 0),
                reorder_level=data.get('reorder_level', 10),
                gst_percentage=Decimal(str(data.get('gst_percentage', 0)))
            )
            db.session.add(product)
            db.session.commit()
            return jsonify(product.to_dict()), 201
    
    @app.route('/api/products/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    def product_detail(id):
        product = Product.query.get_or_404(id)
        
        if request.method == 'GET':
            return jsonify(product.to_dict())
        
        elif request.method == 'PUT':
            data = request.get_json()
            product.product_name = data.get('product_name', product.product_name)
            product.description = data.get('description', product.description)
            product.category_id = data.get('category_id', product.category_id)
            product.unit = data.get('unit', product.unit)
            product.purchase_price = Decimal(str(data.get('purchase_price', product.purchase_price)))
            product.selling_price = Decimal(str(data.get('selling_price', product.selling_price)))
            product.quantity_in_stock = data.get('quantity_in_stock', product.quantity_in_stock)
            product.reorder_level = data.get('reorder_level', product.reorder_level)
            product.gst_percentage = Decimal(str(data.get('gst_percentage', product.gst_percentage)))
            db.session.commit()
            return jsonify(product.to_dict())
        
        elif request.method == 'DELETE':
            product.is_active = False
            db.session.commit()
            return '', 204
    
    # ==================== CUSTOMERS ====================
    @app.route('/api/customers', methods=['GET', 'POST'])
    def customers():
        if request.method == 'GET':
            customers = Customer.query.filter_by(is_active=True).all()
            return jsonify([cust.to_dict() for cust in customers])
        
        elif request.method == 'POST':
            data = request.get_json()
            customer = Customer(
                customer_code=generate_customer_code(),
                customer_name=data.get('customer_name'),
                customer_phone=data.get('customer_phone', ''),
                customer_email=data.get('customer_email', ''),
                customer_address=data.get('customer_address', ''),
                customer_city=data.get('customer_city', ''),
                gst_number=data.get('gst_number', ''),
                credit_limit=Decimal(str(data.get('credit_limit', 0))),
                opening_balance=Decimal(str(data.get('opening_balance', 0)))
            )
            db.session.add(customer)
            db.session.commit()
            return jsonify(customer.to_dict()), 201
    
    @app.route('/api/customers/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    def customer_detail(id):
        customer = Customer.query.get_or_404(id)
        
        if request.method == 'GET':
            return jsonify(customer.to_dict())
        
        elif request.method == 'PUT':
            data = request.get_json()
            customer.customer_name = data.get('customer_name', customer.customer_name)
            customer.customer_phone = data.get('customer_phone', customer.customer_phone)
            customer.customer_email = data.get('customer_email', customer.customer_email)
            customer.customer_address = data.get('customer_address', customer.customer_address)
            customer.customer_city = data.get('customer_city', customer.customer_city)
            customer.gst_number = data.get('gst_number', customer.gst_number)
            customer.credit_limit = Decimal(str(data.get('credit_limit', customer.credit_limit)))
            db.session.commit()
            return jsonify(customer.to_dict())
        
        elif request.method == 'DELETE':
            customer.is_active = False
            db.session.commit()
            return '', 204
    
    # ==================== INVOICES ====================
    @app.route('/invoices')
    @login_required
    def invoices_page():
        return render_template('invoices.html')

    @app.route('/edit-invoice/<int:id>')
    @login_required
    def edit_invoice_page(id):
        invoice = Invoice.query.get_or_404(id)
        return render_template('invoice_edit.html', invoice=invoice)

    @app.route('/api/invoices', methods=['GET', 'POST'])
    def invoices():
        if request.method == 'GET':
            invoices = Invoice.query.order_by(Invoice.invoice_date.desc()).limit(200).all()
            return jsonify([inv.to_dict(with_items=True) for inv in invoices])

        data = request.get_json() or {}
        customer_id_raw = data.get('customer_id')
        if not customer_id_raw:
            return jsonify({'error': 'customer_id is required'}), 400
        try:
            customer_id = int(customer_id_raw)
        except Exception:
            return jsonify({'error': 'Invalid customer_id'}), 400

        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 400

        items_data = data.get('items')
        if not isinstance(items_data, list) or len(items_data) == 0:
            return jsonify({'error': 'At least one invoice item is required'}), 400

        try:
            # invoice date
            if data.get('invoice_date'):
                try:
                    invoice_date = datetime.strptime(str(data.get('invoice_date')), '%Y-%m-%d')
                except Exception:
                    invoice_date = datetime.utcnow()
            else:
                invoice_date = datetime.utcnow()

            # create invoice
            inv_number = generate_invoice_number()
            tries = 0
            while Invoice.query.filter_by(invoice_number=inv_number).first() and tries < 5:
                inv_number = generate_invoice_number()
                tries += 1

            new_invoice = Invoice(
                invoice_number=inv_number,
                customer_id=customer_id,
                invoice_date=invoice_date,
                payment_method=str(data.get('payment_method') or 'Cash'),
                po_number=str(data.get('po_number') or ''),
                status=str(data.get('status') or 'Finalized'),
                notes=str(data.get('notes') or '')
            )
            db.session.add(new_invoice)
            db.session.flush()

            # Accept discount and transport charges from payload (default 0)
            try:
                new_invoice.discount = Decimal(str(data.get('discount', 0) or 0))
            except Exception:
                new_invoice.discount = Decimal('0.00')
            try:
                new_invoice.transport_charges = Decimal(str(data.get('transport_charges', 0) or 0))
            except Exception:
                new_invoice.transport_charges = Decimal('0.00')

            inv_subtotal = Decimal('0.00')
            inv_total_tax = Decimal('0.00')

            for idx, it in enumerate(items_data):
                prod_id_raw = it.get('product_id')
                try:
                    prod_id = int(prod_id_raw)
                except Exception:
                    db.session.rollback()
                    return jsonify({'error': f'Invalid product_id in item {idx+1}'}), 400

                product = Product.query.get(prod_id)
                if not product:
                    db.session.rollback()
                    return jsonify({'error': f'Product not found in item {idx+1}'}), 400

                try:
                    qty = Decimal(str(it.get('quantity') if it.get('quantity') is not None else 1))
                except Exception:
                    db.session.rollback()
                    return jsonify({'error': f'Invalid quantity in item {idx+1}'}), 400
                if qty <= 0:
                    db.session.rollback()
                    return jsonify({'error': f'Quantity must be > 0 in item {idx+1}'}), 400

                try:
                    up_val = it.get('unit_price', None)
                    if up_val is None or str(up_val).strip() == '':
                        unit_price = Decimal(str(getattr(product, 'selling_price', 0) or 0))
                    else:
                        unit_price = Decimal(str(up_val))
                except Exception:
                    db.session.rollback()
                    return jsonify({'error': f'Invalid unit_price in item {idx+1}'}), 400

                try:
                    gst_raw = it.get('gst_percentage', None)
                    if gst_raw is None or str(gst_raw).strip() == '':
                        gst_pct = Decimal(str(getattr(product, 'gst_percentage', 0) or 0))
                    else:
                        gst_pct = Decimal(str(gst_raw))
                except Exception:
                    gst_pct = Decimal(str(getattr(product, 'gst_percentage', 0) or 0))

                if gst_pct < 0 or gst_pct > 100:
                    gst_pct = Decimal(str(getattr(product, 'gst_percentage', 0) or 0))

                # calculations
                line_sub = (qty * unit_price).quantize(Decimal('0.01'))
                total_gst = (line_sub * gst_pct / Decimal('100')).quantize(Decimal('0.01'))
                cgst_pct = (gst_pct / Decimal('2')).quantize(Decimal('0.01'))
                sgst_pct = (gst_pct / Decimal('2')).quantize(Decimal('0.01'))
                cgst_amt = (line_sub * cgst_pct / Decimal('100')).quantize(Decimal('0.01'))
                sgst_amt = (line_sub * sgst_pct / Decimal('100')).quantize(Decimal('0.01'))
                line_total = (line_sub + total_gst).quantize(Decimal('0.01'))

                # finish creating the invoice item, persist and accumulate totals
                item_obj = InvoiceItem(
                    invoice_id=new_invoice.id,
                    product_id=prod_id,
                    quantity=qty,
                    unit_price=unit_price,
                    gst_percentage=gst_pct,
                    gst_amount=total_gst,
                    cgst_percentage=cgst_pct,
                    cgst_amount=cgst_amt,
                    sgst_percentage=sgst_pct,
                    sgst_amount=sgst_amt,
                    line_total=line_total,
                    created_at=datetime.utcnow()
                )
                db.session.add(item_obj)

                inv_subtotal += line_sub
                inv_total_tax += total_gst

            # finalize invoice totals and commit (include transport charges and subtract discount)
            new_invoice.subtotal = inv_subtotal
            new_invoice.total_tax = inv_total_tax
            # compute final amount: subtotal + tax + transport - discount
            try:
                transport = Decimal(str(new_invoice.transport_charges or 0))
            except Exception:
                transport = Decimal('0.00')
            try:
                discount_val = Decimal(str(new_invoice.discount or 0))
            except Exception:
                discount_val = Decimal('0.00')
            total_amt = (inv_subtotal + inv_total_tax + transport - discount_val).quantize(Decimal('0.01'))
            if total_amt < Decimal('0.00'):
                total_amt = Decimal('0.00')
            new_invoice.total_amount = total_amt
            db.session.commit()
            return jsonify(new_invoice.to_dict(with_items=True)), 201
        except Exception as e:
            db.session.rollback()
            app.logger.exception('Error creating invoice')
            return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

    @app.route('/api/invoices/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    def invoice_detail(id):
        invoice = Invoice.query.get_or_404(id)
        if request.method == 'GET':
            return jsonify(invoice.to_dict(with_items=True))

        if request.method == 'DELETE':
            InvoiceItem.query.filter_by(invoice_id=invoice.id).delete()
            db.session.delete(invoice)
            db.session.commit()
            return '', 204

        data = request.get_json() or {}
        try:
            if data.get('customer_id'):
                try:
                    customer_id = int(data.get('customer_id'))
                    cust = Customer.query.get(customer_id)
                    if not cust:
                        return jsonify({'error': 'Customer not found'}), 400
                    invoice.customer_id = customer_id
                except Exception:
                    return jsonify({'error': 'Invalid customer_id'}), 400

            if data.get('invoice_date'):
                try:
                    invoice.invoice_date = datetime.strptime(str(data.get('invoice_date')), '%Y-%m-%d')
                except Exception:
                    pass

            invoice.payment_method = str(data.get('payment_method') or invoice.payment_method)
            invoice.po_number = str(data.get('po_number') or invoice.po_number)
            invoice.status = str(data.get('status') or invoice.status)
            invoice.notes = str(data.get('notes') or invoice.notes)

            items_data = data.get('items')
            if items_data is None:
                db.session.commit()
                return jsonify(invoice.to_dict(with_items=True))

            if not isinstance(items_data, list) or len(items_data) == 0:
                return jsonify({'error': 'At least one invoice item is required'}), 400

            # remove and recreate items
            InvoiceItem.query.filter_by(invoice_id=invoice.id).delete()
            db.session.flush()

            inv_subtotal = Decimal('0.00')
            inv_total_tax = Decimal('0.00')

            for idx, it in enumerate(items_data):
                prod_id_raw = it.get('product_id')
                try:
                    prod_id = int(prod_id_raw)
                except Exception:
                    db.session.rollback()
                    return jsonify({'error': f'Invalid product_id in item {idx+1}'}), 400

                product = Product.query.get(prod_id)
                if not product:
                    db.session.rollback()
                    return jsonify({'error': f'Product not found in item {idx+1}'}), 400

                try:
                    qty = Decimal(str(it.get('quantity') if it.get('quantity') is not None else 1))
                except Exception:
                    db.session.rollback()
                    return jsonify({'error': f'Invalid quantity in item {idx+1}'}), 400
                if qty <= 0:
                    db.session.rollback()
                    return jsonify({'error': f'Quantity must be > 0 in item {idx+1}'}), 400

                try:
                    up_val = it.get('unit_price', None)
                    if up_val is None or str(up_val).strip() == '':
                        unit_price = Decimal(str(getattr(product, 'selling_price', 0) or 0))
                    else:
                        unit_price = Decimal(str(up_val))
                except Exception:
                    db.session.rollback()
                    return jsonify({'error': f'Invalid unit_price in item {idx+1}'}), 400

                try:
                    gst_raw = it.get('gst_percentage', None)
                    if gst_raw is None or str(gst_raw).strip() == '':
                        gst_pct = Decimal(str(getattr(product, 'gst_percentage', 0) or 0))
                    else:
                        gst_pct = Decimal(str(gst_raw))
                except Exception:
                    gst_pct = Decimal(str(getattr(product, 'gst_percentage', 0) or 0))

                if gst_pct < 0 or gst_pct > 100:
                    gst_pct = Decimal(str(getattr(product, 'gst_percentage', 0) or 0))

                line_sub = (qty * unit_price).quantize(Decimal('0.01'))
                total_gst = (line_sub * gst_pct / Decimal('100')).quantize(Decimal('0.01'))
                cgst_pct = (gst_pct / Decimal('2')).quantize(Decimal('0.01'))
                sgst_pct = (gst_pct / Decimal('2')).quantize(Decimal('0.01'))
                cgst_amt = (line_sub * cgst_pct / Decimal('100')).quantize(Decimal('0.01'))
                sgst_amt = (line_sub * sgst_pct / Decimal('100')).quantize(Decimal('0.01'))
                line_total = (line_sub + total_gst).quantize(Decimal('0.01'))

                new_item = InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=prod_id,
                    quantity=qty,
                    unit_price=unit_price,
                    gst_percentage=gst_pct,
                    gst_amount=total_gst,
                    cgst_percentage=cgst_pct,
                    cgst_amount=cgst_amt,
                    sgst_percentage=sgst_pct,
                    sgst_amount=sgst_amt,
                    line_total=line_total,
                    created_at=datetime.utcnow()
                )
                db.session.add(new_item)

                inv_subtotal += line_sub
                inv_total_tax += total_gst

            invoice.subtotal = inv_subtotal
            invoice.total_tax = inv_total_tax
            # include transport_charges and discount if provided in update payload
            try:
                invoice.transport_charges = Decimal(str(data.get('transport_charges', invoice.transport_charges or 0) or 0))
            except Exception:
                invoice.transport_charges = Decimal('0.00')
            try:
                invoice.discount = Decimal(str(data.get('discount', invoice.discount or 0) or 0))
            except Exception:
                invoice.discount = Decimal('0.00')
            try:
                transport = Decimal(str(invoice.transport_charges or 0))
            except Exception:
                transport = Decimal('0.00')
            try:
                discount_val = Decimal(str(invoice.discount or 0))
            except Exception:
                discount_val = Decimal('0.00')
            total_amt = (inv_subtotal + inv_total_tax + transport - discount_val).quantize(Decimal('0.01'))
            if total_amt < Decimal('0.00'):
                total_amt = Decimal('0.00')
            invoice.total_amount = total_amt
            db.session.commit()
            return jsonify(invoice.to_dict(with_items=True))

        except Exception as e:
            db.session.rollback()
            app.logger.exception('Error updating invoice')
            return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

    @app.route('/api/invoices/<int:id>/print')
    def invoice_print(id):
        invoice = Invoice.query.get_or_404(id)
        return render_template('invoice_print.html', invoice=invoice)

    @app.route('/api/invoices/<int:id>/download-pdf', methods=['GET'])
    def download_invoice_pdf(id):
        """Serve the original stored invoice PDF (three-copy print) from temp/ if available and multi-page.
        If not available, render the invoice_print_multi.html template and convert to PDF (WeasyPrint/pdfkit) so the downloaded PDF matches the original HTML print (three copies).
        """
        invoice = Invoice.query.get_or_404(id)
        project_root = os.path.dirname(os.path.abspath(__file__))
        temp_dir = os.path.join(os.path.dirname(project_root), 'temp')
        try:
            # 1) Try to find existing original PDF in temp/
            candidates = []
            if os.path.isdir(temp_dir):
                for fname in os.listdir(temp_dir):
                    if not fname.lower().endswith('.pdf'):
                        continue
                    # prefer filenames that contain the invoice number
                    if invoice.invoice_number and invoice.invoice_number.lower() in fname.lower():
                        candidates.append(os.path.join(temp_dir, fname))
                # fallback: any invoice_*.pdf
                if not candidates:
                    for fname in os.listdir(temp_dir):
                        lname = fname.lower()
                        if lname.startswith('invoice_') or 'invoice' in lname:
                            candidates.append(os.path.join(temp_dir, fname))

            # helper to choose best candidate by page count (prefer >=3)
            def choose_best_by_pages(paths):
                try:
                    from PyPDF2 import PdfReader
                except Exception:
                    PdfReader = None
                best = None
                best_pages = 0
                if PdfReader:
                    for p in paths:
                        try:
                            reader = PdfReader(p)
                            # PyPDF2: reader.pages is sequence
                            pages_count = len(getattr(reader, 'pages', []))
                        except Exception:
                            pages_count = 0
                        if pages_count >= 3:
                            return p, pages_count
                        if pages_count > best_pages:
                            best = p
                            best_pages = pages_count
                # if no reader or no pages info, pick most recent
                if not best and paths:
                    paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                    return paths[0], 0
                return best, best_pages

            selected = None
            selected_pages = 0
            if candidates:
                selected, selected_pages = choose_best_by_pages(candidates)

            if selected:
                app.logger.info('Serving stored invoice PDF for invoice %s (id=%s): %s (pages=%s)',
                                invoice.invoice_number, id, os.path.basename(selected), selected_pages)
                return send_file(selected, as_attachment=True, download_name=os.path.basename(selected), mimetype='application/pdf')

            # 2) No suitable stored PDF found — render HTML template and convert to PDF (three copies)
            # Render the multi-copy HTML (use invoice_print_multi.html if present, otherwise invoice_print.html)
            tpl_name = 'invoice_print_multi.html' if os.path.exists(os.path.join(project_root, 'templates', 'invoice_print_multi.html')) else 'invoice_print.html'
            html = render_template(tpl_name, invoice=invoice)

            # Try WeasyPrint first (pure Python, good HTML fidelity)
            pdf_bytes = None
            try:
                from weasyprint import HTML
                pdf_bytes = HTML(string=html, base_url=project_root).write_pdf()
                app.logger.info('Generated PDF from HTML using WeasyPrint for invoice %s (id=%s)', invoice.invoice_number, id)
            except Exception as e:
                app.logger.info('WeasyPrint unavailable or failed: %s', str(e))

            # Fallback to pdfkit (requires wkhtmltopdf binary)
            if pdf_bytes is None:
                try:
                    import pdfkit
                    # common options: disable local file access restrictions
                    options = {
                        'enable-local-file-access': None,
                        'quiet': ''
                    }
                    pdf_bytes = pdfkit.from_string(html, False, options=options)
                    app.logger.info('Generated PDF from HTML using pdfkit for invoice %s (id=%s)', invoice.invoice_number, id)
                except Exception as e:
                    app.logger.info('pdfkit unavailable or failed: %s', str(e))

            # Final fallback: revert to programmatic ReportLab generator (ensure 3 pages)
            if pdf_bytes is None:
                try:
                    from io import BytesIO
                    from reportlab.pdfgen import canvas
                    from reportlab.lib.pagesizes import A4
                    from reportlab.lib import colors

                    buffer = BytesIO()
                    c = canvas.Canvas(buffer, pagesize=A4)
                    width, height = A4

                    # Use the invoice_print_multi.html rendered HTML as guidance; keep simple: draw the HTML as plain text lines
                    # For best results, prefer WeasyPrint/pdfkit. This ReportLab fallback will draw basic three pages with invoice number header.
                    for copy_label in ['COPY 1 - ORIGINAL FOR RECIPIENT', 'COPY 2 - DUPLICATE FOR SUPPLIER', 'COPY 3 - TRIPLICATE FOR TRANSPORTER']:
                        c.setFont('Helvetica-Bold', 12)
                        c.drawString(50, height - 50, copy_label)
                        c.setFont('Helvetica', 9)
                        c.drawString(50, height - 70, f'Invoice: {invoice.invoice_number}   Date: {invoice.invoice_date.strftime("%d-%m-%Y") if invoice.invoice_date else "N/A"}')
                        # Minimal items table
                        y = height - 110
                        c.setFont('Helvetica-Bold', 10)
                        c.drawString(50, y, 'Product')
                        c.drawString(300, y, 'Qty')
                        c.drawString(350, y, 'Rate')
                        c.drawString(420, y, 'Amount')
                        y -= 16
                        c.setFont('Helvetica', 9)
                        for item in invoice.items:
                            c.drawString(50, y, getattr(item.product, 'product_name', 'Product'))
                            c.drawString(300, y, f"{float(item.quantity):.2f}")
                            c.drawString(350, y, f"{float(item.unit_price):.2f}")
                            c.drawString(420, y, f"{float(item.line_total):.2f}")
                            y -= 14
                            if y < 120:
                                break
                        c.showPage()
                    c.save()
                    buffer.seek(0)
                    pdf_bytes = buffer.read()
                    app.logger.info('Generated PDF using ReportLab fallback for invoice %s (id=%s)', invoice.invoice_number, id)
                except Exception as e:
                    app.logger.exception('ReportLab fallback failed')
                    return jsonify({'error': 'Unable to generate PDF', 'details': str(e)}), 500

            # Send generated PDF bytes
            return send_file(BytesIO(pdf_bytes), as_attachment=True, download_name=f'invoice_{invoice.invoice_number}.pdf', mimetype='application/pdf')

        except Exception as e:
            app.logger.exception('Error preparing invoice PDF')
            return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

    @app.route('/customers')
    @login_required
    def customers_page():
        return render_template('customers.html')

    @app.route('/products')
    @login_required
    def products_page():
        return render_template('products.html')

    @app.route('/settings')
    @login_required
    def settings_page():
        shop = ShopInfo.query.first()
        return render_template('settings.html', shop=shop)
    
    @app.route('/sales')
    @login_required
    def sales_page():
        return render_template('sales.html')

    @app.route('/api/customers/<int:id>/profile')
    def customer_profile(id):
        customer = Customer.query.get_or_404(id)
        invoices = Invoice.query.filter_by(customer_id=id).order_by(Invoice.invoice_date.desc()).all()
        payments = Payment.query.join(Invoice).filter(Invoice.customer_id == id).order_by(Payment.payment_date.desc()).all()
        
        # Calculate analytics
        total_spent = sum(inv.total_amount for inv in invoices if inv.status == 'Finalized')
        total_paid = sum(pay.amount for pay in payments)
        outstanding_balance = total_spent - total_paid
        
        analytics = {
            'total_spent': total_spent,
            'total_paid': total_paid,
            'outstanding_balance': outstanding_balance
        }
        
        return jsonify({
            'customer': customer.to_dict(),
            'analytics': analytics,
            'invoices': [inv.to_dict() for inv in invoices],
            'payments': [pay.to_dict() for pay in payments]
        })

    # ==================== PAYMENTS ====================
    @app.route('/api/payments', methods=['GET', 'POST'])
    def payments():
        if request.method == 'GET':
            payments = Payment.query.order_by(Payment.payment_date.desc()).all()
            return jsonify([pay.to_dict() for pay in payments])

        elif request.method == 'POST':
            data = request.get_json()

            # Determine invoice_id: prefer explicit invoice_id, otherwise accept customer_id and attach
            invoice_id = data.get('invoice_id')
            if not invoice_id and data.get('customer_id'):
                try:
                    cust_id = int(data.get('customer_id'))
                except Exception:
                    return jsonify({'error': 'Invalid customer_id'}), 400
                # find earliest unpaid invoice for the customer, fallback to most recent invoice
                invoice = Invoice.query.filter(Invoice.customer_id == cust_id).filter(Invoice.payment_status != 'Paid').order_by(Invoice.invoice_date.asc()).first()
                if not invoice:
                    invoice = Invoice.query.filter_by(customer_id=cust_id).order_by(Invoice.invoice_date.desc()).first()
                if not invoice:
                    return jsonify({'error': 'No invoice found for customer to attach payment'}), 400
                invoice_id = invoice.id

            if not invoice_id:
                return jsonify({'error': 'invoice_id or customer_id is required'}), 400

            # parse payment_date
            try:
                payment_date = datetime.strptime(data.get('payment_date'), '%Y-%m-%d') if data.get('payment_date') else datetime.utcnow()
            except Exception:
                payment_date = datetime.utcnow()

            try:
                amount = Decimal(str(data.get('amount')))
            except Exception:
                return jsonify({'error': 'Invalid amount'}), 400

            payment = Payment(
                invoice_id=invoice_id,
                payment_date=payment_date,
                payment_method=data.get('payment_method', 'Cash'),
                amount=amount,
                reference_number=data.get('reference_number', ''),
                notes=data.get('notes', '')
            )
            db.session.add(payment)
            db.session.commit()

            # Update invoice payment status based on payments total
            try:
                inv = Invoice.query.get(payment.invoice_id)
                if inv:
                    total_paid = sum(Decimal(str(p.amount or 0)) for p in inv.payments) if inv.payments else Decimal('0')
                    inv_total = Decimal(str(inv.total_amount or 0))
                    if total_paid >= inv_total and inv_total > 0:
                        inv.payment_status = 'Paid'
                    elif total_paid > 0:
                        inv.payment_status = 'Partially Paid'
                    else:
                        inv.payment_status = 'Unpaid'
                    db.session.commit()
            except Exception:
                db.session.rollback()

            return jsonify(payment.to_dict()), 201

    @app.route('/api/payments/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    def payment_detail(id):
        payment = Payment.query.get_or_404(id)
        if request.method == 'GET':
            return jsonify(payment.to_dict())

        elif request.method == 'PUT':
            data = request.get_json()
            payment.payment_date = datetime.strptime(data.get('payment_date'), '%Y-%m-%d')
            payment.payment_method = data.get('payment_method', payment.payment_method)
            payment.amount = Decimal(str(data.get('amount', payment.amount)))
            payment.reference_number = data.get('reference_number', payment.reference_number)
            payment.notes = data.get('notes', payment.notes)
            db.session.commit()
            return jsonify(payment.to_dict())

        elif request.method == 'DELETE':
            db.session.delete(payment)
            db.session.commit()
            return '', 204

    # ==================== EXPENSES ====================
    @app.route('/api/expenses', methods=['GET', 'POST'])
    def expenses():
        if request.method == 'GET':
            expenses = Expense.query.order_by(Expense.expense_date.desc()).all()
            return jsonify([exp.to_dict() for exp in expenses])

        elif request.method == 'POST':
            data = request.get_json()
            expense = Expense(
                expense_date=datetime.strptime(data.get('expense_date'), '%Y-%m-%d'),
                category_id=data.get('category_id'),
                amount=Decimal(str(data.get('amount'))),
                description=data.get('description', '')
            )
            db.session.add(expense)
            db.session.commit()
            return jsonify(expense.to_dict()), 201

    @app.route('/api/expenses/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    def expense_detail(id):
        expense = Expense.query.get_or_404(id)
        if request.method == 'GET':
            return jsonify(expense.to_dict())

        elif request.method == 'PUT':
            data = request.get_json()
            expense.expense_date = datetime.strptime(data.get('expense_date'), '%Y-%m-%d')
            expense.category_id = data.get('category_id', expense.category_id)
            expense.amount = Decimal(str(data.get('amount', expense.amount)))
            expense.description = data.get('description', expense.description)
            db.session.commit()
            return jsonify(expense.to_dict())

        elif request.method == 'DELETE':
            db.session.delete(expense)
            db.session.commit()
            return '', 204

    # ==================== REPORTS ====================
    @app.route('/reports')
    @login_required
    def reports_page():
        return render_template('reports.html')

    @app.route('/api/reports/sales', methods=['GET'])
    def reports_sales():
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        q = Invoice.query
        if start_date:
            try:
                sd = datetime.strptime(start_date, '%Y-%m-%d')
                q = q.filter(Invoice.invoice_date >= sd)
            except Exception:
                pass
        if end_date:
            try:
                ed = datetime.strptime(end_date, '%Y-%m-%d')
                q = q.filter(Invoice.invoice_date <= ed)
            except Exception:
                pass
        invoices = q.all()
        total = sum([float(inv.total_amount or 0) for inv in invoices])
        return jsonify({'total': total, 'count': len(invoices)})

    @app.route('/api/reports/customers', methods=['GET'])
    def reports_customers():
        customers = Customer.query.filter_by(is_active=True).all()
        return jsonify([c.to_dict() for c in customers])

    @app.route('/api/reports/products', methods=['GET'])
    def reports_products():
        products = Product.query.filter_by(is_active=True).all()
        return jsonify([p.to_dict() for p in products])

    # Sales by customer (used by reports UI)
    @app.route('/api/sales/customers', methods=['GET'])
    def sales_by_customers():
        # Return per-customer aggregates suitable for the frontend table
        customers = Customer.query.filter_by(is_active=True).all()
        results = []
        for c in customers:
            invoices = Invoice.query.filter_by(customer_id=c.id).all()
            payments = Payment.query.join(Invoice, Payment.invoice_id == Invoice.id).filter(Invoice.customer_id == c.id).all()
            invoice_count = len(invoices)
            total_purchases = float(sum(Decimal(str(inv.total_amount or 0)) for inv in invoices)) if invoices else 0.0
            total_paid = float(sum(Decimal(str(p.amount or 0)) for p in payments)) if payments else 0.0
            balance = total_purchases - total_paid
            results.append({
                'id': c.id,
                'customer_id': c.id,
                'customer_name': c.customer_name,
                'customer_phone': c.customer_phone,
                'customer_city': c.customer_city,
                'invoice_count': invoice_count,
                'total_purchases': total_purchases,
                'total_paid': total_paid,
                'balance': balance
            })
        return jsonify(results)

    @app.route('/api/sales/customer/<int:id>/ledger', methods=['GET'])
    def sales_customer_ledger(id):
        # Return customer details, invoice list and a merged ledger (invoices + payments)
        customer = Customer.query.get_or_404(id)
        invoices = Invoice.query.filter_by(customer_id=id).order_by(Invoice.invoice_date.asc()).all()
        payments = Payment.query.join(Invoice, Payment.invoice_id == Invoice.id).filter(Invoice.customer_id == id).order_by(Payment.payment_date.asc()).all()

        # Compute totals
        total_purchases = sum(Decimal(str(inv.total_amount or 0)) for inv in invoices) if invoices else Decimal('0')
        total_paid = sum(Decimal(str(p.amount or 0)) for p in payments) if payments else Decimal('0')
        balance = total_purchases - total_paid

        # Build ledger entries chronological (ascending), compute running balance starting from opening_balance
        ledger_entries = []
        opening_balance = Decimal(str(getattr(customer, 'opening_balance', 0) or 0))
        running = opening_balance

        # prepare unified list with date, type and amount
        combined = []
        for inv in invoices:
            combined.append({'date': inv.invoice_date or datetime.utcnow(), 'type': 'invoice', 'ref': inv, 'amount': Decimal(str(inv.total_amount or 0))})
        for p in payments:
            combined.append({'date': p.payment_date or datetime.utcnow(), 'type': 'payment', 'ref': p, 'amount': Decimal(str(p.amount or 0))})

        combined.sort(key=lambda x: x['date'] or datetime.utcnow())

        for entry in combined:
            if entry['type'] == 'invoice':
                inv = entry['ref']
                running += entry['amount']
                ledger_entries.append({
                    'date': entry['date'].strftime('%Y-%m-%d') if entry['date'] else '',
                    'type': 'Invoice',
                    'invoice_number': inv.invoice_number,
                    'ref': inv.invoice_number,
                    'debit': float(entry['amount']),
                    'credit': 0.0,
                    'balance': float(running),
                    'status': inv.payment_status if hasattr(inv, 'payment_status') else getattr(inv, 'status', '')
                })
            else:
                p = entry['ref']
                running -= entry['amount']
                ledger_entries.append({
                    'date': entry['date'].strftime('%Y-%m-%d') if entry['date'] else '',
                    'type': 'Payment',
                    'invoice_number': p.reference_number if getattr(p, 'reference_number', None) else f'PAY-{p.id}',
                    'ref': p.reference_number if getattr(p, 'reference_number', None) else f'PAY-{p.id}',
                    'debit': 0.0,
                    'credit': float(entry['amount']),
                    'balance': float(running),
                    'status': 'Payment'
                })

        # return data for frontend with helpful summary fields
        return jsonify({
            'customer': customer.to_dict(),
            'invoices': [inv.to_dict() for inv in invoices][::-1],  # most recent first
            'payments': [p.to_dict() for p in payments][::-1],
            'ledger': ledger_entries[::-1],  # return most recent first
            'total_purchases': float(total_purchases),
            'total_paid': float(total_paid),
            'balance': float(balance)
        })

    @app.route('/api/sales/customer/<int:id>/ledger/pdf')
    def sales_customer_ledger_pdf(id):
        # Generate PDF ledger for customer (in-memory) and return as attachment
        customer = Customer.query.get_or_404(id)
        invoices = Invoice.query.filter_by(customer_id=id).order_by(Invoice.invoice_date.asc()).all()
        payments = Payment.query.join(Invoice, Payment.invoice_id == Invoice.id).filter(Invoice.customer_id == id).order_by(Payment.payment_date.asc()).all()

        from io import BytesIO
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4

        pdf_io = BytesIO()
        c = canvas.Canvas(pdf_io, pagesize=A4)
        width, height = A4
        margin = 40
        y = height - margin

        c.setFont('Helvetica-Bold', 16)
        c.drawString(margin, y, f'Customer Sales Report - {customer.customer_name}')
        y -= 24

        c.setFont('Helvetica', 10)
        c.drawString(margin, y, f'Customer Code: {customer.customer_code or ""}')
        c.drawString(margin + 300, y, f'Date: {datetime.now().strftime("%d-%m-%Y")}')
        y -= 18

        # Summary totals
        total_purchases = sum(Decimal(str(inv.total_amount or 0)) for inv in invoices) if invoices else Decimal('0')
        total_paid = sum(Decimal(str(p.amount or 0)) for p in payments) if payments else Decimal('0')
        total_pending = total_purchases - total_paid

        c.setFont('Helvetica-Bold', 11)
        c.drawString(margin, y, f'Total Purchases: ₹{float(total_purchases):.2f}')
        y -= 14
        c.drawString(margin, y, f'Total Paid: ₹{float(total_paid):.2f}')
        y -= 14
        c.drawString(margin, y, f'Total Pending: ₹{float(total_pending):.2f}')
        y -= 20

        # Table header
        c.setFont('Helvetica-Bold', 10)
        c.drawString(margin, y, 'Invoice')
        c.drawString(margin + 120, y, 'Date')
        c.drawString(margin + 220, y, 'Amount')
        c.drawString(margin + 320, y, 'Paid')
        c.drawString(margin + 420, y, 'Pending')
        c.drawString(margin + 500, y, 'Status')
        y -= 12
        c.line(margin, y, width - margin, y)
        y -= 12

        c.setFont('Helvetica', 9)
        for inv in invoices:
            paid_amount = sum(Decimal(str(p.amount)) for p in inv.payments) if inv.payments else Decimal('0')
            pending = Decimal(str(inv.total_amount or 0)) - paid_amount
            if y < 60:
                c.showPage()
                y = height - margin
                c.setFont('Helvetica', 9)
            c.drawString(margin, y, inv.invoice_number or '')
            c.drawString(margin + 120, y, inv.invoice_date.strftime('%Y-%m-%d') if inv.invoice_date else '')
            c.drawRightString(margin + 300, y, f'₹{float(inv.total_amount or 0):.2f}')
            c.drawRightString(margin + 400, y, f'₹{float(paid_amount):.2f}')
            c.drawRightString(margin + 500, y, f'₹{float(pending):.2f}')
            c.drawString(margin + 520, y, inv.payment_status if hasattr(inv, 'payment_status') else getattr(inv, 'status', ''))
            y -= 14

        # Footer
        if y < 120:
            c.showPage()
            y = height - margin
        c.setFont('Helvetica-Bold', 10)
        c.drawString(margin, y - 10, f'Report Generated: {datetime.now().strftime("%d %B %Y at %I:%M %p")}')

        c.showPage()
        c.save()
        pdf_io.seek(0)

        filename = f'sales_report_{customer.customer_name.replace(" ", "_")}_{datetime.now().strftime("%d-%m-%Y")}.pdf'
        return send_file(pdf_io, download_name=filename, as_attachment=True, mimetype='application/pdf')

    @app.route('/api/sales/customer/<int:id>/whatsapp-share', methods=['GET', 'POST'])
    def sales_customer_whatsapp_share(id):
        # Prepare a shareable WhatsApp URL with customer's phone number
        customer = Customer.query.get_or_404(id)
        invoices = Invoice.query.filter_by(customer_id=id).all()
        payments = Payment.query.join(Invoice, Payment.invoice_id == Invoice.id).filter(Invoice.customer_id == id).all()

        total_purchases = sum(Decimal(str(inv.total_amount or 0)) for inv in invoices) if invoices else Decimal('0')
        total_paid = sum(Decimal(str(p.amount or 0)) for p in payments) if payments else Decimal('0')
        total_pending = total_purchases - total_paid

        # Link to the PDF endpoint (will download when opened in browser)
        base = request.url_root.rstrip('/')
        pdf_link = f"{base}/api/sales/customer/{id}/ledger/pdf"

        message = (
            f"📊 *Customer Sales Report*\n\n"
            f"Customer: {customer.customer_name}\n"
            f"Total Purchases: ₹{float(total_purchases):.2f}\n"
            f"Total Paid: ₹{float(total_paid):.2f}\n"
            f"Total Pending: ₹{float(total_pending):.2f}\n\n"
            f"📄 Download detailed report: {pdf_link}"
        )

        # Use customer's phone number if available
        phone_number = customer.customer_phone
        if phone_number:
            # Clean phone number - remove spaces, dashes, parentheses
            phone_number = phone_number.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            # Add country code if not present (assuming India +91)
            if not phone_number.startswith('+') and len(phone_number) == 10:
                phone_number = f'+91{phone_number}'
            whatsapp_url = f"https://wa.me/{phone_number}?text={quote(message)}"
        else:
            # Fallback to generic WhatsApp if no phone number
            whatsapp_url = f"https://wa.me/?text={quote(message)}"

        return jsonify({'success': True, 'whatsapp_url': whatsapp_url, 'message': message, 'phone_number': phone_number})

    @app.route('/api/invoices/<int:id>/update', methods=['PUT', 'PATCH'])
    def update_invoice(id):
        invoice = Invoice.query.get_or_404(id)
        try:
            data = request.get_json() or {}

            # Update simple header fields if provided
            if data.get('invoice_date'):
                try:
                    invoice.invoice_date = datetime.strptime(str(data.get('invoice_date')), '%Y-%m-%d')
                except Exception:
                    pass

            if data.get('customer_id'):
                try:
                    cid = int(data.get('customer_id'))
                    cust = Customer.query.get(cid)
                    if cust:
                        invoice.customer_id = cid
                except Exception:
                    pass

            # Text fields
            for field in ['po_number', 'challan_no', 'transport_mode', 'vehicle_number', 'contact_person', 'e_weighment', 'pay_terms', 'payment_method', 'status', 'notes']:
                if field in data:
                    setattr(invoice, field, data.get(field) if data.get(field) is not None else getattr(invoice, field))

            # If items provided, replace invoice items
            items_data = data.get('items', None)
            if items_data is not None:
                if not isinstance(items_data, list) or len(items_data) == 0:
                    return jsonify({'success': False, 'error': 'At least one invoice item is required'}), 400

                # remove existing items using relationship so session stays consistent
                invoice.items[:] = []
                db.session.flush()

                inv_subtotal = Decimal('0.00')
                inv_total_tax = Decimal('0.00')

                for idx, it in enumerate(items_data):
                    prod_id_raw = it.get('product_id')
                    try:
                        prod_id = int(prod_id_raw)
                    except Exception:
                        db.session.rollback()
                        return jsonify({'success': False, 'error': f'Invalid product_id in item {idx+1}'}), 400

                    product = Product.query.get(prod_id)
                    if not product:
                        db.session.rollback()
                        return jsonify({'success': False, 'error': f'Product not found in item {idx+1}'}), 400

                    try:
                        qty = Decimal(str(it.get('quantity') if it.get('quantity') is not None else 1))
                    except Exception:
                        db.session.rollback()
                        return jsonify({'success': False, 'error': f'Invalid quantity in item {idx+1}'}), 400
                    if qty <= 0:
                        db.session.rollback()
                        return jsonify({'success': False, 'error': f'Quantity must be > 0 in item {idx+1}'}), 400

                    try:
                        up_val = it.get('unit_price', None)
                        if up_val is None or str(up_val).strip() == '':
                            unit_price = Decimal(str(getattr(product, 'selling_price', 0) or 0))
                        else:
                            unit_price = Decimal(str(up_val))
                    except Exception:
                        db.session.rollback()
                        return jsonify({'success': False, 'error': f'Invalid unit_price in item {idx+1}'}), 400

                    try:
                        gst_raw = it.get('gst_percentage', None)
                        if gst_raw is None or str(gst_raw).strip() == '':
                            gst_pct = Decimal(str(getattr(product, 'gst_percentage', 0) or 0))
                        else:
                            gst_pct = Decimal(str(gst_raw))
                    except Exception:
                        gst_pct = Decimal(str(getattr(product, 'gst_percentage', 0) or 0))

                    if gst_pct < 0 or gst_pct > 100:
                        gst_pct = Decimal(str(getattr(product, 'gst_percentage', 0) or 0))

                    # calculations
                    line_sub = (qty * unit_price).quantize(Decimal('0.01'))
                    total_gst = (line_sub * gst_pct / Decimal('100')).quantize(Decimal('0.01'))
                    cgst_pct = (gst_pct / Decimal('2')).quantize(Decimal('0.01'))
                    sgst_pct = (gst_pct / Decimal('2')).quantize(Decimal('0.01'))
                    cgst_amt = (line_sub * cgst_pct / Decimal('100')).quantize(Decimal('0.01'))
                    sgst_amt = (line_sub * sgst_pct / Decimal('100')).quantize(Decimal('0.01'))
                    line_total = (line_sub + total_gst).quantize(Decimal('0.01'))

                    new_item = InvoiceItem(
                        invoice_id=invoice.id,
                        product_id=prod_id,
                        quantity=qty,
                        unit_price=unit_price,
                        gst_percentage=gst_pct,
                        gst_amount=total_gst,
                        cgst_percentage=cgst_pct,
                        cgst_amount=cgst_amt,
                        sgst_percentage=sgst_pct,
                        sgst_amount=sgst_amt,
                        line_total=line_total,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(new_item)

                    inv_subtotal += line_sub
                    inv_total_tax += total_gst

            invoice.subtotal = inv_subtotal
            invoice.total_tax = inv_total_tax
            # include transport_charges and discount if provided in update payload
            try:
                invoice.transport_charges = Decimal(str(data.get('transport_charges', invoice.transport_charges or 0) or 0))
            except Exception:
                invoice.transport_charges = Decimal('0.00')
            try:
                invoice.discount = Decimal(str(data.get('discount', invoice.discount or 0) or 0))
            except Exception:
                invoice.discount = Decimal('0.00')
            try:
                transport = Decimal(str(invoice.transport_charges or 0))
            except Exception:
                transport = Decimal('0.00')
            try:
                discount_val = Decimal(str(invoice.discount or 0))
            except Exception:
                discount_val = Decimal('0.00')
            total_amt = (inv_subtotal + inv_total_tax + transport - discount_val).quantize(Decimal('0.01'))
            if total_amt < Decimal('0.00'):
                total_amt = Decimal('0.00')
            invoice.total_amount = total_amt
            db.session.commit()
            return jsonify({'success': True, 'invoice': invoice.to_dict(with_items=True)})

        except Exception as e:
            db.session.rollback()
            app.logger.exception('Error updating invoice')
            return jsonify({'success': False, 'error': str(e)}), 500

    return app
