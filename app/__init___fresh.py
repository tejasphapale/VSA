from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from sqlalchemy import func

from app.models import db, ShopInfo, Category, Product, Customer, Invoice, InvoiceItem, Payment, Expense
from app.utils import generate_invoice_number, generate_product_code, generate_customer_code, amount_in_words

def create_app():
    basedir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.dirname(basedir)
    
    app = Flask(__name__, 
                template_folder=os.path.join(project_root, 'templates'),
                static_folder=os.path.join(project_root, 'static'))
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(project_root, "data", "billing.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    app.jinja_env.globals.update(amount_in_words=amount_in_words)
    
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
    
    # ==================== INVOICES ====================
    @app.route('/invoices')
    def invoices_page():
        return render_template('invoices.html')
    
    @app.route('/api/invoices', methods=['GET', 'POST'])
    def invoices():
        if request.method == 'GET':
            invoices = Invoice.query.order_by(Invoice.invoice_date.desc()).limit(100).all()
            return jsonify([inv.to_dict(with_items=True) for inv in invoices])
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                invoice = Invoice(
                    invoice_number=generate_invoice_number(),
                    invoice_date=datetime.strptime(data.get('invoice_date', datetime.utcnow().isoformat()), '%Y-%m-%d').date(),
                    customer_id=data.get('customer_id'),
                    po_number=data.get('po_number', '2627574'),
                    status='Draft'
                )
                db.session.add(invoice)
                db.session.flush()
                
                for item in data.get('items', []):
                    inv_item = InvoiceItem(
                        invoice_id=invoice.id,
                        product_id=item['product_id'],
                        quantity=Decimal(str(item['quantity'])),
                        unit_price=Decimal(str(item['unit_price'])),
                        gst_percentage=Decimal(str(item.get('gst_percentage', 18)))
                    )
                    db.session.add(inv_item)
                
                db.session.commit()
                return jsonify(invoice.to_dict(with_items=True)), 201
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': str(e)}), 400
    
    @app.route('/api/invoices/<int:id>', methods=['GET'])
    def invoice_detail(id):
        invoice = Invoice.query.get_or_404(id)
        return jsonify(invoice.to_dict(with_items=True))
    
    @app.route('/api/invoices/<int:id>/finalize', methods=['PUT'])
    def finalize_invoice(id):
        invoice = Invoice.query.get_or_404(id)
        if invoice.status == 'Finalized':
            return jsonify({'error': 'Invoice already finalized'}), 400
        for item in invoice.items:
            item.product.quantity_in_stock -= int(item.quantity)
        invoice.status = 'Finalized'
        invoice.payment_status = 'Unpaid'
        db.session.commit()
        return jsonify(invoice.to_dict(with_items=True))
    
    @app.route('/api/invoices/<int:id>/print', methods=['GET'])
    def print_invoice(id):
        invoice = Invoice.query.get_or_404(id)
        shop = ShopInfo.query.first()
        return render_template('invoice_print.html', invoice=invoice, shop=shop)
    
    @app.route('/api/invoices/<int:id>/download-pdf', methods=['GET'])
    def download_invoice_pdf(id):
        try:
            invoice = Invoice.query.get_or_404(id)
            pdf_buffer = BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=A4)
            width, height = A4
            
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "TAX INVOICE")
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, height - 80, "VS ABRASIVE PRODUCTS")
            c.setFont("Helvetica", 9)
            c.drawString(50, height - 95, "GSTIN: 27AKLPG5978N1Z9")
            
            c.setFont("Helvetica-Bold", 10)
            y = height - 130
            c.drawString(50, y, f"Invoice: {invoice.invoice_number}")
            c.drawString(300, y, f"Date: {invoice.invoice_date.strftime('%d-%m-%Y') if invoice.invoice_date else 'N/A'}")
            
            y -= 30
            if invoice.customer:
                c.drawString(50, y, f"Bill To: {invoice.customer.customer_name}")
                y -= 15
                c.drawString(50, y, invoice.customer.customer_address)
                y -= 15
                c.drawString(50, y, f"GSTIN: {invoice.customer.gst_number if invoice.customer.gst_number else 'Unregistered'}")
            
            y -= 25
            c.setFont("Helvetica-Bold", 9)
            c.drawString(50, y, "SL.")
            c.drawString(80, y, "PRODUCT")
            c.drawString(350, y, "QTY")
            c.drawString(410, y, "RATE")
            c.drawString(470, y, "AMOUNT")
            
            y -= 10
            c.line(50, y, 570, y)
            
            c.setFont("Helvetica", 8)
            y -= 15
            for idx, item in enumerate(invoice.items, 1):
                c.drawString(50, y, str(idx))
                c.drawString(80, y, item.product.product_name if item.product else 'Product')
                c.drawString(350, y, f"{item.quantity:.2f}")
                c.drawString(410, y, f"₹{item.unit_price:.2f}")
                c.drawString(470, y, f"₹{item.line_total:.2f}")
                y -= 12
                if y < 80:
                    c.showPage()
                    y = height - 50
            
            y -= 10
            c.line(50, y, 570, y)
            y -= 15
            c.setFont("Helvetica-Bold", 10)
            c.drawString(400, y, f"Subtotal: ₹{invoice.subtotal:.2f}")
            y -= 15
            c.drawString(400, y, f"Tax: ₹{invoice.total_tax:.2f}")
            y -= 15
            c.drawString(400, y, f"TOTAL: ₹{invoice.total_amount:.2f}")
            
            c.setFont("Helvetica", 8)
            c.drawString(50, 30, f"Generated: {datetime.now().strftime('%d %B %Y')}")
            
            c.save()
            pdf_buffer.seek(0)
            
            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=f"invoice_{invoice.invoice_number}.pdf",
                mimetype='application/pdf'
            )
        except Exception as e:
            return jsonify({'error': f'PDF error: {str(e)}'}), 500
    
    @app.route('/api/invoices/<int:id>/edit', methods=['GET'])
    def edit_invoice_page(id):
        invoice = Invoice.query.get_or_404(id)
        return render_template('invoice_edit.html', invoice=invoice)
    
    @app.route('/api/invoices/<int:id>/update', methods=['PUT'])
    def update_invoice(id):
        invoice = Invoice.query.get_or_404(id)
        try:
            data = request.get_json()
            if 'invoice_date' in data and data['invoice_date']:
                invoice.invoice_date = datetime.strptime(str(data['invoice_date']), '%Y-%m-%d').date()
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
            
            if 'items' in data:
                for item in invoice.items:
                    db.session.delete(item)
                
                for item_data in data['items']:
                    item = InvoiceItem(
                        invoice_id=invoice.id,
                        product_id=item_data['product_id'],
                        quantity=Decimal(str(item_data['quantity'])),
                        unit_price=Decimal(str(item_data['unit_price'])),
                        gst_percentage=Decimal(str(item_data['gst_percentage']))
                    )
                    db.session.add(item)
            
            db.session.commit()
            return jsonify({'success': True, 'invoice': invoice.to_dict(with_items=True)})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/invoices/<int:id>/delete', methods=['DELETE'])
    def delete_invoice(id):
        invoice = Invoice.query.get_or_404(id)
        db.session.delete(invoice)
        db.session.commit()
        return '', 204
    
    # ==================== SALES & LEDGER ====================
    @app.route('/api/sales/customers', methods=['GET'])
    def sales_customers():
        customers = Customer.query.filter_by(is_active=True).all()
        result = []
        for customer in customers:
            invoices = Invoice.query.filter_by(customer_id=customer.id, status='Finalized').all()
            total_purchases = sum(Decimal(str(inv.total_amount)) for inv in invoices) if invoices else Decimal('0')
            payments = Payment.query.join(Invoice).filter(Invoice.customer_id == customer.id).all()
            total_paid = sum(Decimal(str(p.amount)) for p in payments) if payments else Decimal('0')
            balance = total_purchases - total_paid
            
            result.append({
                'id': customer.id,
                'customer_name': customer.customer_name,
                'customer_phone': customer.customer_phone,
                'customer_city': customer.customer_city,
                'gst_number': customer.gst_number,
                'total_purchases': float(total_purchases),
                'total_paid': float(total_paid),
                'balance': float(balance)
            })
        return jsonify(result)
    
    @app.route('/api/sales/customer/<int:customer_id>/ledger', methods=['GET'])
    def customer_ledger(customer_id):
        customer = Customer.query.get_or_404(customer_id)
        invoices = Invoice.query.filter_by(customer_id=customer_id, status='Finalized').all()
        payments = Payment.query.join(Invoice).filter(Invoice.customer_id == customer_id).all()
        
        ledger_entries = []
        running_balance = Decimal('0')
        
        entries = []
        for inv in invoices:
            entries.append(('invoice', inv.invoice_date, inv))
        for pay in payments:
            entries.append(('payment', pay.payment_date, pay))
        
        entries.sort(key=lambda x: x[1])
        
        for entry_type, date, item in entries:
            if entry_type == 'invoice':
                amount = Decimal(str(item.total_amount))
                running_balance += amount
                ledger_entries.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'type': 'Invoice',
                    'description': f"Invoice {item.invoice_number}",
                    'debit': float(amount),
                    'credit': 0,
                    'balance': float(running_balance),
                    'reference': item.invoice_number
                })
            else:
                amount = Decimal(str(item.amount))
                running_balance -= amount
                ledger_entries.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'type': 'Payment',
                    'description': 'Payment received',
                    'debit': 0,
                    'credit': float(amount),
                    'balance': float(running_balance),
                    'reference': item.payment_number or f"PAY-{item.id}"
                })
        
        return jsonify({
            'customer': customer.to_dict(),
            'ledger': ledger_entries,
            'total_purchases': float(sum(Decimal(str(inv.total_amount)) for inv in invoices)),
            'total_paid': float(sum(Decimal(str(p.amount)) for p in payments)),
            'balance': float(running_balance)
        })
    
    @app.route('/api/sales/customer/<int:customer_id>/ledger/pdf', methods=['GET'])
    def customer_ledger_pdf(customer_id):
        """Generate and download customer sales report as PDF"""
        try:
            customer = Customer.query.get_or_404(customer_id)
            invoices = Invoice.query.filter_by(customer_id=customer_id, status='Finalized').all()
            payments = Payment.query.join(Invoice).filter(Invoice.customer_id == customer_id).all()
            
            total_purchases = sum(Decimal(str(inv.total_amount)) for inv in invoices) if invoices else Decimal('0')
            total_paid = sum(Decimal(str(p.amount)) for p in payments) if payments else Decimal('0')
            total_pending = total_purchases - total_paid
            
            pdf_buffer = BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=A4)
            width, height = A4
            
            # Title
            c.setFont("Helvetica-Bold", 18)
            c.drawString(50, height - 40, "CUSTOMER SALES REPORT")
            
            # Company info
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, height - 65, "VS ABRASIVE PRODUCTS")
            c.setFont("Helvetica", 8)
            c.drawString(50, height - 78, "GSTIN: 27AKLPG5978N1Z9 | MSME: UDYAM-MH-01-0202254")
            
            # Customer info
            c.setFont("Helvetica-Bold", 11)
            y_pos = height - 120
            c.drawString(50, y_pos, f"Customer: {customer.customer_name}")
            y_pos -= 15
            c.setFont("Helvetica", 9)
            c.drawString(50, y_pos, f"Code: {customer.customer_code} | Phone: {customer.customer_phone if customer.customer_phone else 'N/A'}")
            y_pos -= 12
            c.drawString(50, y_pos, f"Address: {customer.customer_address}, {customer.customer_city}")
            y_pos -= 12
            c.drawString(50, y_pos, f"GSTIN: {customer.gst_number if customer.gst_number else 'Unregistered'}")
            
            # Summary
            y_pos -= 25
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y_pos, "FINANCIAL SUMMARY")
            y_pos -= 3
            c.line(50, y_pos, 550, y_pos)
            y_pos -= 15
            
            c.setFont("Helvetica", 9)
            c.drawString(50, y_pos, f"Total Purchases: ₹{float(total_purchases):,.2f}")
            y_pos -= 12
            c.drawString(50, y_pos, f"Total Paid: ₹{float(total_paid):,.2f}")
            y_pos -= 12
            c.drawString(50, y_pos, f"Balance Pending: ₹{float(total_pending):,.2f}")
            
            # Table
            y_pos -= 25
            c.setFont("Helvetica-Bold", 9)
            c.drawString(50, y_pos, "Invoice #")
            c.drawString(130, y_pos, "Date")
            c.drawString(200, y_pos, "Amount")
            c.drawString(280, y_pos, "Paid")
            c.drawString(360, y_pos, "Pending")
            c.drawString(450, y_pos, "Status")
            
            y_pos -= 3
            c.line(50, y_pos, 550, y_pos)
            y_pos -= 12
            
            c.setFont("Helvetica", 8)
            for invoice in invoices:
                paid = sum(Decimal(str(p.amount)) for p in invoice.payments) if invoice.payments else Decimal('0')
                pending = Decimal(str(invoice.total_amount)) - paid
                
                c.drawString(50, y_pos, invoice.invoice_number)
                c.drawString(130, y_pos, invoice.invoice_date.strftime('%d-%m-%Y') if invoice.invoice_date else 'N/A')
                c.drawString(200, y_pos, f"₹{float(invoice.total_amount):,.2f}")
                c.drawString(280, y_pos, f"₹{float(paid):,.2f}")
                c.drawString(360, y_pos, f"₹{float(pending):,.2f}")
                c.drawString(450, y_pos, invoice.payment_status)
                
                y_pos -= 12
                if y_pos < 50:
                    c.showPage()
                    y_pos = height - 50
            
            c.setFont("Helvetica", 7)
            c.drawString(50, 20, f"Generated: {datetime.now().strftime('%d/%m/%Y at %H:%M:%S')}")
            c.drawString(300, 20, "For Official Use Only")
            
            c.save()
            pdf_buffer.seek(0)
            
            filename = f"sales_report_{customer.customer_name.replace(' ', '_')}_{datetime.now().strftime('%d-%m-%Y')}.pdf"
            return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500
    
    # ==================== PRODUCTS ====================
    @app.route('/api/products', methods=['GET', 'POST'])
    def products():
        if request.method == 'GET':
            products = Product.query.filter_by(is_active=True).all()
            return jsonify([p.to_dict() for p in products])
        
        elif request.method == 'POST':
            data = request.get_json()
            product = Product(
                product_code=generate_product_code(),
                product_name=data.get('product_name'),
                description=data.get('description', ''),
                cost_price=Decimal(str(data.get('cost_price', 0))),
                selling_price=Decimal(str(data.get('selling_price', 0))),
                gst_percentage=Decimal(str(data.get('gst_percentage', 18))),
                quantity_in_stock=int(data.get('quantity_in_stock', 0)),
                reorder_level=int(data.get('reorder_level', 10))
            )
            db.session.add(product)
            db.session.commit()
            return jsonify(product.to_dict()), 201
    
    # ==================== CUSTOMERS ====================
    @app.route('/api/customers', methods=['GET', 'POST'])
    def customers():
        if request.method == 'GET':
            customers = Customer.query.filter_by(is_active=True).all()
            return jsonify([c.to_dict() for c in customers])
        
        elif request.method == 'POST':
            data = request.get_json()
            customer = Customer(
                customer_code=generate_customer_code(),
                customer_name=data.get('customer_name'),
                customer_phone=data.get('customer_phone', ''),
                customer_email=data.get('customer_email', ''),
                customer_address=data.get('customer_address', ''),
                customer_city=data.get('customer_city', ''),
                gst_number=data.get('gst_number', '')
            )
            db.session.add(customer)
            db.session.commit()
            return jsonify(customer.to_dict()), 201
    
    # ==================== PAGES ====================
    @app.route('/invoices')
    def invoices_page_():
        return render_template('invoices.html')
    
    @app.route('/products')
    def products_page():
        return render_template('products.html')
    
    @app.route('/customers')
    def customers_page():
        return render_template('customers.html')
    
    @app.route('/reports')
    def reports_page():
        return render_template('reports.html')
    
    return app
