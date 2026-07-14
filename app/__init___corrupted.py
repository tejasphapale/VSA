from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
from decimal import Decimal
import os
from app.models import db, ShopInfo, Category, Product, Customer, Invoice, InvoiceItem, Payment, Expense
from app.utils import generate_invoice_number, generate_product_code, generate_customer_code, amount_in_words
from sqlalchemy import func

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
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    # Number to Words Converter
    def amount_in_words(amount):
        """Convert amount to words"""
        try:
            amount = float(amount)
            if amount == 0:
                return "Zero Rupees Only"
            
            ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
            tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
            teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
            scales = ['', 'Thousand', 'Million', 'Billion']
            
            def convert_hundreds(num):
                result = ''
                hundreds = int(num / 100)
                if hundreds > 0:
                    result += ones[hundreds] + ' Hundred '
                
                remainder = num % 100
                if remainder >= 20:
                    result += tens[int(remainder / 10)] + ' '
                    units = remainder % 10
                    if units > 0:
                        result += ones[units] + ' '
                elif remainder >= 10:
                    result += teens[remainder - 10] + ' '
                elif remainder > 0:
                    result += ones[remainder] + ' '
                
                return result
            
            # Split into rupees and paise
            rupees = int(amount)
            paise = int(round((amount - rupees) * 100))
            
            words = ''
            scale_index = 0
            
            while rupees > 0:
                if rupees % 1000 != 0:
                    words = convert_hundreds(rupees % 1000).strip() + ' ' + scales[scale_index] + ' ' + words
                rupees = int(rupees / 1000)
                scale_index += 1
            
            words = words.strip()
            if paise > 0:
                words += ' And ' + convert_hundreds(paise).strip() + 'Paise'
            
            return words.replace('  ', ' ').strip() + ' Rupees Only'
        except:
            return "Amount in Words"
    
    app.jinja_env.filters['amount_words'] = amount_in_words
    app.jinja_env.globals['amount_in_words'] = amount_in_words
    
    # ==================== DASHBOARD ====================
    @app.route('/')
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
    
    @app.route('/api/sales/customers', methods=['GET'])
    def sales_customers():
        """Get customers with balance and payment status for sales dashboard"""
        customers = Customer.query.filter_by(is_active=True).all()
        result = []
        
        for customer in customers:
            # Calculate total spent
            total_spent = db.session.query(func.sum(Invoice.total_amount)).filter_by(customer_id=customer.id).scalar() or 0
            
            # Calculate total paid
            total_paid = db.session.query(func.sum(Payment.amount)).join(Invoice).filter(Invoice.customer_id == customer.id).scalar() or 0
            
            # Calculate balance
            balance = total_spent - total_paid
            
            # Get last transaction date
            last_invoice = Invoice.query.filter_by(customer_id=customer.id).order_by(Invoice.invoice_date.desc()).first()
            last_transaction = last_invoice.invoice_date if last_invoice else None
            
            result.append({
                'id': customer.id,
                'customer_code': customer.customer_code,
                'customer_name': customer.customer_name,
                'customer_phone': customer.customer_phone,
                'customer_email': customer.customer_email,
                'customer_city': customer.customer_city,
                'customer_address': customer.customer_address,
                'gst_number': customer.gst_number,
                'credit_limit': float(customer.credit_limit),
                'balance': float(balance),
                'total_spent': float(total_spent),
                'total_paid': float(total_paid),
                'last_transaction': last_transaction.isoformat() if last_transaction else None,
                'is_active': customer.is_active
            })
        
        return jsonify(result)
    
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
    def invoices_page():
        return render_template('invoices.html')
    
    @app.route('/api/invoices', methods=['GET', 'POST'])
    def invoices():
        if request.method == 'GET':
            page = request.args.get('page', 1, type=int)
        
        elif request.method == 'POST':
            data = request.get_json()
            
            invoice = Invoice(
                invoice_number=generate_invoice_number(),
                customer_id=data.get('customer_id'),
                invoice_date=datetime.strptime(data.get('invoice_date', datetime.utcnow().isoformat()), '%Y-%m-%d'),
                payment_method=data.get('payment_method', 'Cash'),
                status='Draft',
                notes=data.get('notes', ''),
                po_number=data.get('po_number'),
                challan_no=data.get('challan_no'),
                date_of_supply=datetime.strptime(data.get('date_of_supply'), '%Y-%m-%d') if data.get('date_of_supply') else None,
                place_of_supply=data.get('place_of_supply', 'Sangamner'),
                state=data.get('state', 'Maharashtra'),
                transport_mode=data.get('transport_mode', 'BY ROAD'),
                vehicle_number=data.get('vehicle_number'),
                e_weighment=data.get('e_weighment'),
                pay_terms=data.get('pay_terms', '0 Days'),
                contact_person=data.get('contact_person')
            )
            db.session.add(invoice)
            db.session.flush()
            
            items = data.get('items', [])
            subtotal = Decimal('0')
            total_tax = Decimal('0')
            
            for item in items:
                product = Product.query.get(item['product_id'])
                if not product:
                    db.session.rollback()
                    return jsonify({'error': f"Product {item['product_id']} not found"}), 400
                
                quantity = Decimal(str(item.get('quantity', 1)))
                unit_price = Decimal(str(item.get('unit_price', product.selling_price)))
                gst_percent = Decimal(str(item.get('gst_percentage', product.gst_percentage)))
                
                # Calculate CGST and SGST (half of GST each for intra-state)
                cgst_percent = gst_percent / 2
                sgst_percent = gst_percent / 2
                
                line_subtotal = quantity * unit_price
                gst_amount = line_subtotal * gst_percent / 100
                cgst_amount = line_subtotal * cgst_percent / 100
                sgst_amount = line_subtotal * sgst_percent / 100
                line_total = line_subtotal + gst_amount
                
                invoice_item = InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    gst_percentage=gst_percent,
                    cgst_percentage=cgst_percent,
                    sgst_percentage=sgst_percent,
                    gst_amount=gst_amount,
                    cgst_amount=cgst_amount,
                    sgst_amount=sgst_amount,
                    line_total=line_total
                )
                db.session.add(invoice_item)
                subtotal += line_subtotal
                total_tax += gst_amount
            
            discount = Decimal(str(data.get('discount', 0)))
            invoice.subtotal = subtotal
            invoice.total_tax = total_tax
            invoice.discount = discount
            invoice.total_amount = subtotal + total_tax - discount
            
            db.session.commit()
            return jsonify(invoice.to_dict(with_items=True)), 201
    
    @app.route('/api/invoices/<int:id>', methods=['GET'])
    def invoice_detail(id):
        invoice = Invoice.query.get_or_404(id)
        return jsonify(invoice.to_dict(with_items=True))
    
    @app.route('/api/invoices/<int:id>/finalize', methods=['PUT'])
    def finalize_invoice(id):
        invoice = Invoice.query.get_or_404(id)
        
        if invoice.status == 'Finalized':
            return jsonify({'error': 'Invoice is already finalized'}), 400
        
        # Update product stock
        for item in invoice.items:
            item.product.quantity_in_stock -= int(item.quantity)
        
        invoice.status = 'Finalized'
        invoice.payment_status = 'Unpaid'
        db.session.commit()
        
        return jsonify(invoice.to_dict(with_items=True))
    
    @app.route('/api/invoices/<int:id>/cancel', methods=['PUT'])
    def cancel_invoice(id):
        invoice = Invoice.query.get_or_404(id)
        
        if invoice.status == 'Cancelled':
            return jsonify({'error': 'Invoice is already cancelled'}), 400
        
        invoice.status = 'Cancelled'
        db.session.commit()
        
        return jsonify(invoice.to_dict(with_items=True))
    
    @app.route('/api/invoices/<int:id>/print', methods=['GET'])
    def print_invoice(id):
        invoice = Invoice.query.get_or_404(id)
        shop = ShopInfo.query.first()
        return render_template('invoice_print_single.html', invoice=invoice, shop=shop, amount_in_words=amount_in_words)
    
    @app.route('/api/invoices/<int:id>/print-multi', methods=['GET'])
    def print_invoice_multi(id):
        invoice = Invoice.query.get_or_404(id)
        shop = ShopInfo.query.first()
        return render_template('invoice_print_new.html', invoice=invoice, shop=shop, amount_in_words=amount_in_words)
    
    # Edit Invoice Page
    @app.route('/api/invoices/<int:id>/edit', methods=['GET'])
    def edit_invoice(id):
        invoice = Invoice.query.get_or_404(id)
        customers = Customer.query.filter_by(is_active=True).all()
        return render_template('invoice_edit.html', invoice=invoice, customers=customers)
    
    # Update Invoice
    @app.route('/api/invoices/<int:id>/update', methods=['PUT'])
    def update_invoice(id):
        invoice = Invoice.query.get_or_404(id)
        data = request.get_json()
        
        try:
            if 'invoice_date' in data and data['invoice_date']:
                invoice.invoice_date = datetime.strptime(data['invoice_date'], '%Y-%m-%d').date()
            
            if 'po_number' in data:
                invoice.po_number = data['po_number']
            
            if 'challan_no' in data:
                invoice.challan_no = data['challan_no']
            
            if 'transport_mode' in data:
                invoice.transport_mode = data['transport_mode']
            
            if 'vehicle_number' in data:
                invoice.vehicle_number = data['vehicle_number']
            
            if 'contact_person' in data:
                invoice.contact_person = data['contact_person']
            
            if 'e_weighment' in data:
                invoice.e_weighment = data['e_weighment']
            
            if 'pay_terms' in data:
                invoice.pay_terms = data['pay_terms']
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Invoice updated successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    @app.route('/api/invoices/<int:id>', methods=['PUT'])
    def update_invoice_full(id):
        """Full invoice update including items"""
        invoice = Invoice.query.get_or_404(id)
        data = request.get_json()
        
        try:
            # Update basic invoice fields
            if 'invoice_date' in data and data['invoice_date']:
                invoice.invoice_date = datetime.strptime(data['invoice_date'], '%Y-%m-%d')
            
            if 'customer_id' in data:
                invoice.customer_id = data['customer_id']
            
            if 'payment_method' in data:
                invoice.payment_method = data['payment_method']
            
            if 'notes' in data:
                invoice.notes = data['notes']
            
            # Update items if provided
            if 'items' in data:
                # Delete existing items
                InvoiceItem.query.filter_by(invoice_id=invoice.id).delete()
                
                # Add new items
                subtotal = Decimal('0')
                total_tax = Decimal('0')
                
                for item_data in data['items']:
                    product = Product.query.get(item_data.get('product_id')) if item_data.get('product_id') else None
                    
                    quantity = Decimal(str(item_data.get('quantity', 0)))
                    unit_price = Decimal(str(item_data.get('unit_price', 0)))
                    gst_percent = Decimal(str(item_data.get('gst_percentage', 0)))
                    
                    # Calculate CGST and SGST (half of GST each for intra-state)
                    cgst_percent = gst_percent / 2
                    sgst_percent = gst_percent / 2
                    
                    line_subtotal = quantity * unit_price
                    gst_amount = line_subtotal * gst_percent / 100
                    cgst_amount = line_subtotal * cgst_percent / 100
                    sgst_amount = line_subtotal * sgst_percent / 100
                    line_total = line_subtotal + gst_amount
                    
                    invoice_item = InvoiceItem(
                        invoice_id=invoice.id,
                        product_id=product.id if product else None,
                        quantity=quantity,
                        unit_price=unit_price,
                        gst_percentage=gst_percent,
                        cgst_percentage=cgst_percent,
                        sgst_percentage=sgst_percent,
                        gst_amount=gst_amount,
                        cgst_amount=cgst_amount,
                        sgst_amount=sgst_amount,
                        line_total=line_total
                    )
                    db.session.add(invoice_item)
                    subtotal += line_subtotal
                    total_tax += gst_amount
                
                invoice.subtotal = subtotal
                invoice.total_tax = total_tax
                invoice.total_amount = subtotal + total_tax - invoice.discount
            
            db.session.commit()
            return jsonify(invoice.to_dict(with_items=True))
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    
    # ==================== PAYMENTS ====================
    @app.route('/api/payments', methods=['POST'])
    def add_payment():
        data = request.get_json()
        invoice = Invoice.query.get_or_404(data.get('invoice_id'))
        
        amount = Decimal(str(data.get('amount')))
        payment = Payment(
            invoice_id=invoice.id,
            payment_date=datetime.strptime(data.get('payment_date', datetime.utcnow().isoformat()), '%Y-%m-%d'),
            amount=amount,
            payment_method=data.get('payment_method', 'Cash'),
            reference_number=data.get('reference_number', ''),
            notes=data.get('notes', '')
        )
        
        db.session.add(payment)
        
        # Update payment status
        total_paid = sum(Decimal(str(p.amount)) for p in invoice.payments) + amount
        invoice.payment_status = 'Paid' if total_paid >= invoice.total_amount else 'Partial'
        
        db.session.commit()
        return jsonify(payment.to_dict()), 201
    
    @app.route('/api/invoices/<int:id>/payments', methods=['GET'])
    def invoice_payments(id):
        invoice = Invoice.query.get_or_404(id)
        return jsonify([p.to_dict() for p in invoice.payments])
    
    # ==================== EXPENSES ====================
    @app.route('/api/expenses', methods=['GET', 'POST'])
    def expenses():
        if request.method == 'GET':
            expenses = Expense.query.order_by(Expense.expense_date.desc()).limit(100).all()
            return jsonify([exp.to_dict() for exp in expenses])
        
        elif request.method == 'POST':
            data = request.get_json()
            expense = Expense(
                expense_date=datetime.strptime(data.get('expense_date', datetime.utcnow().isoformat()), '%Y-%m-%d'),
                category=data.get('category'),
                amount=Decimal(str(data.get('amount'))),
                description=data.get('description', ''),
                payment_method=data.get('payment_method', 'Cash'),
                reference_number=data.get('reference_number', '')
            )
            db.session.add(expense)
            db.session.commit()
            return jsonify(expense.to_dict()), 201
    
    # ==================== REPORTS ====================
    @app.route('/reports')
    def reports():
        return render_template('reports.html')
    
    @app.route('/api/reports/sales', methods=['GET'])
    def sales_report():
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Invoice.query.filter_by(status='Finalized')
        
        if start_date:
            query = query.filter(db.func.date(Invoice.invoice_date) >= start_date)
        if end_date:
            query = query.filter(db.func.date(Invoice.invoice_date) <= end_date)
        
        invoices = query.all()
        
        total_sales = sum(Decimal(str(inv.total_amount)) for inv in invoices)
        total_tax = sum(Decimal(str(inv.total_tax)) for inv in invoices)
        total_discount = sum(Decimal(str(inv.discount)) for inv in invoices)
        
        return jsonify({
            'total_sales': float(total_sales),
            'total_tax': float(total_tax),
            'total_discount': float(total_discount),
            'invoice_count': len(invoices),
            'invoices': [inv.to_dict() for inv in invoices]
        })
    
    @app.route('/api/reports/inventory', methods=['GET'])
    def inventory_report():
        products = Product.query.filter_by(is_active=True).all()
        low_stock = [p for p in products if p.quantity_in_stock <= p.reorder_level]
        
        total_value = sum(Decimal(str(p.quantity_in_stock)) * Decimal(str(p.purchase_price)) for p in products)
        
        return jsonify({
            'total_products': len(products),
            'low_stock_count': len(low_stock),
            'total_inventory_value': float(total_value),
            'low_stock_items': [p.to_dict() for p in low_stock],
            'all_products': [p.to_dict() for p in products]
        })
    
    @app.route('/api/reports/customer', methods=['GET'])
    def customer_report():
        customers = Customer.query.filter_by(is_active=True).all()
        
        customer_data = []
        for customer in customers:
            total_purchases = sum(Decimal(str(inv.total_amount)) for inv in customer.invoices if inv.status == 'Finalized')
            total_paid = sum(Decimal(str(p.amount)) for inv in customer.invoices for p in inv.payments)
            outstanding = total_purchases - total_paid
            
            customer_data.append({
                'customer_id': customer.id,
                'customer_name': customer.customer_name,
                'phone': customer.customer_phone,
                'city': customer.customer_city,
                'total_purchases': float(total_purchases),
                'total_paid': float(total_paid),
                'outstanding': float(outstanding)
            })
        
        return jsonify(customer_data)
    
    # ==================== PAGES ====================
    @app.route('/products')
    def products_page():
        return render_template('products.html')
    
    @app.route('/customers')
    def customers_page():
        return render_template('customers.html')
    
    @app.route('/settings')
    def settings_page():
        return render_template('settings.html')
    
    @app.route('/sales')
    def sales_page():
        return render_template('sales.html')
    
    @app.route('/customers/<int:id>')
    def customer_detail_page(id):
        return render_template('customer_profile.html')
    
    # ==================== CUSTOMER PROFILE ====================
    @app.route('/api/customers/<int:id>/profile', methods=['GET'])
    def customer_profile(id):
        """Get comprehensive customer profile with all transactions, payments, and analytics"""
        customer = Customer.query.get_or_404(id)
        
        # Get all invoices for this customer
        invoices = Invoice.query.filter_by(customer_id=id, status='Finalized').all()
        
        # Calculate totals
        total_spent = Decimal('0')
        total_paid = Decimal('0')
        outstanding_balance = Decimal('0')
        
        invoices_data = []
        for invoice in invoices:
            total_spent += invoice.total_amount
            invoices_data.append({
                'invoice_number': invoice.invoice_number,
                'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d'),
                'due_date': invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else None,
                'total_amount': float(invoice.total_amount),
                'payment_status': invoice.payment_status,
                'items': [item.to_dict() for item in invoice.items]
            })
        
        # Get all payments for this customer
        payments = Payment.query.join(Invoice).filter(Invoice.customer_id == id).all()
        payments_data = []
        for payment in payments:
            total_paid += payment.amount
            payments_data.append({
                'payment_id': payment.id,
                'invoice_number': payment.invoice.invoice_number,
                'payment_date': payment.payment_date.strftime('%Y-%m-%d'),
                'amount': float(payment.amount),
                'payment_method': payment.payment_method,
                'reference_number': payment.reference_number,
                'notes': payment.notes
            })
        
        # Calculate outstanding balance
        outstanding_balance = total_spent - total_paid
        
        # Get credit utilization
        credit_limit = float(customer.credit_limit)
        credit_used = float(outstanding_balance)
        credit_available = credit_limit - credit_used if credit_limit > 0 else 0
        
        profile_data = {
            'customer': customer.to_dict(),
            'analytics': {
                'total_spent': float(total_spent),
                'total_paid': float(total_paid),
                'outstanding_balance': float(outstanding_balance),
                'credit_limit': credit_limit,
                'credit_used': credit_used,
                'credit_available': credit_available,
                'total_invoices': len(invoices),
                'unpaid_invoices': len([inv for inv in invoices if inv.payment_status == 'Unpaid']),
                'total_payments': len(payments)
            },
            'invoices': invoices_data,
            'payments': payments_data
        }
        
        return jsonify(profile_data)
    
    return app
