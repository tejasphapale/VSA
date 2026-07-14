from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from decimal import Decimal


class PDFGenerator:
    def __init__(self, filename):
        self.doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        self.styles = getSampleStyleSheet()
        self.elements = []
        self.width, self.height = A4
        
        # Custom styles
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            spaceBefore=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomRight',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=TA_RIGHT
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomCenter',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER
        ))
        
        # Modern professional styles
        self.styles.add(ParagraphStyle(
            name='ModernTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#1a365d'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='ModernSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='ModernBody',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#4a5568'),
            leading=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='ModernSmall',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#718096'),
            leading=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='StatusPaid',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.white,
            backColor=colors.HexColor('#38a169'),
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='StatusPending',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.white,
            backColor=colors.HexColor('#d69e2e'),
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='StatusPastPending',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.white,
            backColor=colors.HexColor('#e53e3e'),
            alignment=TA_CENTER
        ))
    
    def add_title(self, text):
        self.elements.append(Paragraph(text, self.styles['CustomTitle']))
        self.elements.append(Spacer(1, 0.2 * inch))
    
    def add_heading(self, text):
        self.elements.append(Paragraph(text, self.styles['CustomHeading']))
    
    def add_paragraph(self, text, style='CustomNormal'):
        self.elements.append(Paragraph(text, self.styles[style]))
        self.elements.append(Spacer(1, 0.1 * inch))
    
    def add_table(self, data, headers=None, col_widths=None, style='default'):
        if headers:
            data = [headers] + data
        
        if not col_widths:
            col_widths = [self.width / len(data[0])] * len(data[0])
        
        table = Table(data, colWidths=col_widths)
        
        if style == 'default':
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
        elif style == 'ledger':
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (2, 1), (4, -1), 'RIGHT'),
            ]))
        elif style == 'invoice':
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ]))
        
        self.elements.append(table)
        self.elements.append(Spacer(1, 0.2 * inch))
    
    def add_summary_box(self, label, value, color=colors.HexColor('#667eea')):
        """Add a summary box with label and value"""
        data = [
            [Paragraph(label, self.styles['CustomNormal']), 
             Paragraph(f"<b>{value}</b>", self.styles['CustomRight'])]
        ]
        table = Table(data, colWidths=[3 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        self.elements.append(table)
        self.elements.append(Spacer(1, 0.1 * inch))
    
    def add_horizontal_line(self):
        self.elements.append(Spacer(1, 0.1 * inch))
        self.elements.append(Table([['']], colWidths=[self.width], style=TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.grey),
        ])))
        self.elements.append(Spacer(1, 0.1 * inch))
    
    def add_modern_header(self, title, subtitle="", date=None):
        """Add modern header with title and optional subtitle"""
        self.elements.append(Paragraph(title, self.styles['ModernTitle']))
        if subtitle:
            self.elements.append(Paragraph(subtitle, self.styles['ModernBody']))
        if date:
            self.elements.append(Paragraph(f"Generated: {date}", self.styles['ModernSmall']))
        self.elements.append(Spacer(1, 0.3 * inch))
    
    def add_modern_table(self, data, headers=None, col_widths=None, style='modern'):
        """Add a modern styled table"""
        if headers:
            data = [headers] + data
        
        if not col_widths:
            col_widths = [self.width / len(data[0])] * len(data[0])
        
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        if style == 'modern':
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f7fafc')]),
            ]))
        elif style == 'modern_right':
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (-3, 1), (-1, -1), 'RIGHT'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f7fafc')]),
            ]))
        elif style == 'compact':
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#edf2f7')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (-2, 1), (-1, -1), 'RIGHT'),
            ]))
        
        self.elements.append(table)
        self.elements.append(Spacer(1, 0.15 * inch))
    
    def add_modern_summary_card(self, label, value, color=colors.HexColor('#2c5282'), icon=""):
        """Add a modern summary card"""
        data = [
            [Paragraph(f"<b>{label}</b>", self.styles['ModernSmall']), 
             Paragraph(f"<b>{value}</b>", self.styles['ModernBody'])]
        ]
        table = Table(data, colWidths=[2.5 * inch, 1.5 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#2c5282')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (0, -1), 15),
            ('RIGHTPADDING', (-1, 0), (-1, -1), 15),
        ]))
        self.elements.append(table)
    
    def add_modern_section(self, title):
        """Add a modern section header"""
        self.elements.append(Spacer(1, 0.2 * inch))
        self.elements.append(Paragraph(title, self.styles['ModernSubtitle']))
        self.elements.append(Spacer(1, 0.1 * inch))
    
    def add_modern_footer(self):
        """Add modern footer"""
        self.elements.append(PageBreak())
        self.elements.append(Spacer(1, 1 * inch))
        self.elements.append(Paragraph("─" * 80, self.styles['ModernSmall']))
        self.elements.append(Spacer(1, 0.1 * inch))
        self.elements.append(Paragraph(
            f"This document is computer-generated on {datetime.now().strftime('%d %B %Y at %I:%M %p')}", 
            self.styles['ModernSmall']
        ))
        self.elements.append(Paragraph(
            "For any queries, please contact your business administrator.", 
            self.styles['ModernSmall']
        ))
    
    def generate_customer_ledger(self, customer, ledger_entries, total_purchases, total_paid, balance):
        """Generate customer ledger PDF with payment details"""
        # Header
        self.add_modern_header(
            f"Customer Ledger - {customer['customer_name']}", 
            f"City: {customer.get('customer_city', 'N/A')} | Phone: {customer.get('customer_phone', 'N/A')}",
            datetime.now()
        )
        
        # Summary Cards
        self.elements.append(Spacer(1, 0.2 * inch))
        summary_data = [
            [
                Paragraph("<b>Total Purchases</b>", self.styles['ModernBody']),
                Paragraph(f"<b>₹{total_purchases:.2f}</b>", self.styles['ModernBody']),
                Paragraph("<b>Total Paid</b>", self.styles['ModernBody']),
                Paragraph(f"<b>₹{total_paid:.2f}</b>", self.styles['ModernBody']),
                Paragraph("<b>Balance Due</b>", self.styles['ModernBody']),
                Paragraph(f"<b>₹{balance:.2f}</b>", self.styles['ModernBody'])
            ]
        ]
        summary_table = Table(summary_data, colWidths=[1.2*inch, 0.8*inch, 1.2*inch, 0.8*inch, 1.2*inch, 0.8*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e6f2ff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('ALIGN', (1, 0), (-1, 0), 'RIGHT'),
        ]))
        self.elements.append(summary_table)
        
        # Ledger Table
        self.add_modern_section("Transaction History")
        ledger_data = [['Date', 'Type', 'Description', 'Debit (₹)', 'Credit (₹)', 'Balance (₹)']]
        
        for entry in ledger_entries:
            ledger_data.append([
                entry['date'],
                entry['type'],
                entry['description'],
                f"₹{entry['debit']:.2f}" if entry['debit'] > 0 else "—",
                f"₹{entry['credit']:.2f}" if entry['credit'] > 0 else "—",
                f"₹{entry['balance']:.2f}"
            ])
        
        ledger_col_widths = [0.9*inch, 0.8*inch, 1.5*inch, 1*inch, 1*inch, 1.2*inch]
        self.add_modern_table(ledger_data, col_widths=ledger_col_widths, style='modern_right')
        
        # Footer
        self.elements.append(Spacer(1, 0.3 * inch))
        self.elements.append(Paragraph("─" * 80, self.styles['ModernSmall']))
        self.elements.append(Spacer(1, 0.1 * inch))
        footer_text = f"<b>Outstanding Balance:</b> ₹{balance:.2f}<br/>" \
                     f"<b>Generated:</b> {datetime.now().strftime('%d %B %Y at %I:%M %p')}"
        self.elements.append(Paragraph(footer_text, self.styles['ModernSmall']))
    
    def generate_customer_sales_report(self, customer, invoices, total_sales, total_paid, total_pending):
        """Generate comprehensive customer sales report PDF"""
        # Header
        self.add_modern_header(
            f"📊 Customer Sales Report - {customer['customer_name']}", 
            f"Generated: {datetime.now().strftime('%d %B %Y at %I:%M %p')}",
            datetime.now()
        )
        
        # Customer Information Section
        self.elements.append(Spacer(1, 0.2 * inch))
        self.add_modern_section("📋 Customer Information")
        
        customer_info = [
            [
                Paragraph(f"<b>Customer Name:</b> {customer['customer_name']}", self.styles['ModernBody']),
                Paragraph(f"<b>Customer Code:</b> {customer.get('customer_code', 'N/A')}", self.styles['ModernBody']),
            ],
            [
                Paragraph(f"<b>Phone:</b> {customer.get('customer_phone', 'N/A')}", self.styles['ModernBody']),
                Paragraph(f"<b>City:</b> {customer.get('customer_city', 'N/A')}", self.styles['ModernBody']),
            ],
            [
                Paragraph(f"<b>GSTIN:</b> {customer.get('gst_number', 'Unregistered')}", self.styles['ModernBody']),
                Paragraph(f"<b>Email:</b> {customer.get('customer_email', 'N/A')}", self.styles['ModernBody']),
            ],
        ]
        
        customer_table = Table(customer_info, colWidths=[3.5*inch, 3.5*inch])
        customer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a365d')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        self.elements.append(customer_table)
        
        # Summary Cards
        self.elements.append(Spacer(1, 0.3 * inch))
        self.add_modern_section("💰 Payment Summary")
        
        summary_data = [
            [
                Paragraph("<b>Total Sales</b>", self.styles['ModernBody']),
                Paragraph(f"<b>₹{total_sales:.2f}</b>", self.styles['ModernBody']),
                Paragraph("<b>Total Paid</b>", self.styles['ModernBody']),
                Paragraph(f"<b>₹{total_paid:.2f}</b>", self.styles['ModernBody']),
                Paragraph("<b>Total Pending</b>", self.styles['ModernBody']),
                Paragraph(f"<b>₹{total_pending:.2f}</b>", self.styles['ModernBody']),
            ]
        ]
        
        summary_table = Table(summary_data, colWidths=[1.2*inch, 1*inch, 1.2*inch, 1*inch, 1.2*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e6f2ff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
        ]))
        self.elements.append(summary_table)
        
        # Detailed Orders Table
        self.elements.append(Spacer(1, 0.3 * inch))
        self.add_modern_section("📦 All Orders/Invoices")
        
        if invoices:
            orders_data = [['Invoice #', 'Date', 'Amount', 'Paid', 'Pending', 'Status']]
            
            for invoice in invoices:
                paid = invoice.get('total_paid', 0)
                pending = invoice.get('total_amount', 0) - paid
                status = 'Paid' if pending <= 0 else 'Pending'
                
                orders_data.append([
                    invoice.get('invoice_number', 'N/A'),
                    invoice.get('invoice_date', 'N/A'),
                    f"₹{float(invoice.get('total_amount', 0)):.2f}",
                    f"₹{float(paid):.2f}",
                    f"₹{float(pending):.2f}",
                    status
                ])
            
            orders_col_widths = [1.2*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch]
            self.add_modern_table(orders_data, col_widths=orders_col_widths, style='modern_center')
        else:
            self.elements.append(Paragraph("No invoices found for this customer.", self.styles['ModernBody']))
        
        # Footer with summary
        self.elements.append(Spacer(1, 0.3 * inch))
        self.elements.append(Paragraph("─" * 100, self.styles['ModernSmall']))
        self.elements.append(Spacer(1, 0.1 * inch))
        footer_text = f"<b>Total Orders:</b> {len(invoices)}<br/>" \
                     f"<b>Total Outstanding:</b> ₹{total_pending:.2f}<br/>" \
                     f"<b>Report Generated:</b> {datetime.now().strftime('%d %B %Y at %I:%M %p')}"
        self.elements.append(Paragraph(footer_text, self.styles['ModernSmall']))
    
    def build(self):
        self.doc.build(self.elements)
        return self.doc.filename


def generate_customer_ledger_pdf(customer_data, filename):
    """Generate PDF for customer ledger"""
    pdf = PDFGenerator(filename)
    
    # Title
    pdf.add_title("Customer Ledger Statement")
    
    # Customer Information
    customer = customer_data['customer']
    analytics = customer_data['analytics']
    
    pdf.add_heading("Customer Information")
    customer_info = [
        ['Customer Name:', customer['customer_name']],
        ['Customer Code:', customer['customer_code']],
        ['Phone:', customer['customer_phone'] or 'N/A'],
        ['City:', customer['customer_city'] or 'N/A'],
        ['Email:', customer['customer_email'] or 'N/A'],
    ]
    pdf.add_table(customer_info, col_widths=[2 * inch, 3 * inch])
    
    # Summary
    pdf.add_heading("Account Summary")
    pdf.add_summary_box("Total Purchases", f"₹{analytics['total_spent']:.2f}")
    pdf.add_summary_box("Total Paid", f"₹{analytics['total_paid']:.2f}", colors.HexColor('#28a745'))
    pdf.add_summary_box("Outstanding Balance", f"₹{analytics['outstanding_balance']:.2f}", 
                        colors.HexColor('#dc3545') if analytics['outstanding_balance'] > 0 else colors.HexColor('#28a745'))
    
    # Ledger
    pdf.add_heading("Transaction Ledger")
    ledger_data = []
    for invoice in customer_data['invoices']:
        ledger_data.append([
            invoice['invoice_date'],
            invoice['invoice_number'],
            f"₹{invoice['total_amount']:.2f}",
            f"₹{invoice['amount_paid']:.2f}",
            f"₹{invoice['remaining_balance']:.2f}"
        ])
    
    headers = ['Date', 'Invoice', 'Total', 'Paid', 'Balance']
    col_widths = [1.2 * inch, 1.5 * inch, 1 * inch, 1 * inch, 1 * inch]
    pdf.add_table(ledger_data, headers=headers, col_widths=col_widths, style='ledger')
    
    # Payment History
    if customer_data['payments']:
        pdf.add_heading("Payment History")
        payment_data = []
        for payment in customer_data['payments']:
            payment_data.append([
                payment['payment_date'],
                payment['invoice_number'],
                payment['payment_method'],
                f"₹{payment['amount']:.2f}"
            ])
        
        payment_headers = ['Date', 'Invoice', 'Method', 'Amount']
        payment_col_widths = [1.2 * inch, 1.5 * inch, 1 * inch, 1 * inch]
        pdf.add_table(payment_data, headers=payment_headers, col_widths=payment_col_widths)
    
    # Footer
    pdf.add_horizontal_line()
    pdf.add_paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style='CustomCenter')
    pdf.add_paragraph("This is a computer-generated statement.", style='CustomCenter')
    
    return pdf.build()


def generate_invoice_pdf(invoice_data, shop_info, filename):
    """Generate PDF for single invoice"""
    pdf = PDFGenerator(filename)
    
    # Title
    pdf.add_title("INVOICE")
    
    # Shop Information
    if shop_info:
        pdf.add_heading("From:")
        shop_data = [
            ['Shop Name:', shop_info.get('shop_name', '')],
            ['Phone:', shop_info.get('shop_phone', '')],
            ['Email:', shop_info.get('shop_email', '')],
            ['Address:', shop_info.get('shop_address', '')],
        ]
        pdf.add_table(shop_data, col_widths=[1.5 * inch, 3.5 * inch])
    
    # Invoice Details
    pdf.add_heading("Invoice Details")
    invoice_info = [
        ['Invoice Number:', invoice_data['invoice_number']],
        ['Invoice Date:', invoice_data['invoice_date']],
        ['Customer:', invoice_data.get('customer_name', 'Walk-in Customer')],
        ['Payment Status:', invoice_data['payment_status']],
        ['Payment Method:', invoice_data.get('payment_method', 'N/A')],
    ]
    pdf.add_table(invoice_info, col_widths=[2 * inch, 3 * inch])
    
    # Items
    pdf.add_heading("Invoice Items")
    items_data = []
    for item in invoice_data.get('items', []):
        items_data.append([
            item['product_name'],
            str(item['quantity']),
            f"₹{item['unit_price']:.2f}",
            f"₹{item['gst_amount']:.2f}",
            f"₹{item['line_total']:.2f}"
        ])
    
    item_headers = ['Product', 'Qty', 'Price', 'GST', 'Total']
    item_col_widths = [2 * inch, 0.5 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch]
    pdf.add_table(items_data, headers=item_headers, col_widths=item_col_widths, style='invoice')
    
    # Totals
    pdf.add_heading("Invoice Summary")
    totals_data = [
        ['Subtotal:', f"₹{invoice_data['subtotal']:.2f}"],
        ['Total Tax:', f"₹{invoice_data['total_tax']:.2f}"],
        ['Discount:', f"₹{invoice_data['discount']:.2f}"],
        ['Grand Total:', f"₹{invoice_data['total_amount']:.2f}"],
    ]
    pdf.add_table(totals_data, col_widths=[3 * inch, 2 * inch])
    
    # Footer
    pdf.add_horizontal_line()
    pdf.add_paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style='CustomCenter')
    
    return pdf.build()


def calculate_payment_status(invoice, current_date):
    """Calculate payment status: Paid, Pending, or Past Pending"""
    if invoice.payment_status == 'Paid':
        return 'Paid'
    
    if invoice.due_date and invoice.due_date < current_date:
        return 'Past Pending'
    
    return 'Pending'


def generate_comprehensive_sales_report_pdf(report_data, filename, filter_status=None):
    """Generate comprehensive sales report PDF with modern design"""
    pdf = PDFGenerator(filename)
    
    # Header
    title = "Sales Report"
    subtitle = f"Customer Sales & Payment Details"
    if filter_status:
        subtitle = f"Customer Sales - {filter_status} Status"
    
    pdf.add_modern_header(
        title, 
        subtitle, 
        datetime.now().strftime('%d %B %Y')
    )
    
    # Report Summary
    pdf.add_modern_section("Report Summary")
    
    summary_data = report_data.get('summary', {})
    pdf.add_modern_summary_card("Total Customers", str(summary_data.get('total_customers', 0)), colors.HexColor('#2c5282'))
    pdf.add_modern_summary_card("Total Sales Amount", f"₹{summary_data.get('total_sales', 0):.2f}", colors.HexColor('#38a169'))
    pdf.add_modern_summary_card("Total Collected", f"₹{summary_data.get('total_collected', 0):.2f}", colors.HexColor('#3182ce'))
    pdf.add_modern_summary_card("Outstanding Balance", f"₹{summary_data.get('outstanding_balance', 0):.2f}", colors.HexColor('#e53e3e'))
    
    pdf.elements.append(Spacer(1, 0.2 * inch))
    
    # Customer Details Table
    pdf.add_modern_section("Customer Sales Details")
    
    customers = report_data.get('customers', [])
    if customers:
        customer_table_data = []
        for customer in customers:
            payment_status = customer.get('payment_status', 'Unknown')
            status_color = colors.HexColor('#38a169') if payment_status == 'Paid' else \
                          colors.HexColor('#d69e2e') if payment_status == 'Pending' else \
                          colors.HexColor('#e53e3e') if payment_status == 'Past Pending' else \
                          colors.HexColor('#718096')
            
            customer_table_data.append([
                customer.get('customer_code', ''),
                customer.get('customer_name', ''),
                customer.get('customer_phone', 'N/A'),
                customer.get('customer_city', 'N/A'),
                f"₹{customer.get('total_purchases', 0):.2f}",
                f"₹{customer.get('total_paid', 0):.2f}",
                f"₹{customer.get('outstanding_balance', 0):.2f}",
                payment_status
            ])
        
        headers = ['Code', 'Customer Name', 'Phone', 'City', 'Total Sales', 'Paid', 'Balance', 'Status']
        col_widths = [0.8 * inch, 2 * inch, 1 * inch, 1 * inch, 0.9 * inch, 0.8 * inch, 0.9 * inch, 0.8 * inch]
        pdf.add_modern_table(customer_table_data, headers=headers, col_widths=col_widths, style='modern_right')
    else:
        pdf.add_paragraph("No customers found matching the criteria.", style='ModernBody')
    
    # Detailed Customer Information
    if customers and len(customers) <= 10:  # Only show details if not too many customers
        for customer in customers:
            pdf.elements.append(PageBreak())
            
            # Customer Header
            pdf.add_modern_section(f"Customer: {customer['customer_name']} ({customer['customer_code']})")
            
            # Customer Info
            customer_info = [
                ['Customer Code:', customer.get('customer_code', '')],
                ['Customer Name:', customer.get('customer_name', '')],
                ['Phone:', customer.get('customer_phone', 'N/A')],
                ['Email:', customer.get('customer_email', 'N/A')],
                ['Address:', customer.get('customer_address', 'N/A')],
                ['City:', customer.get('customer_city', 'N/A')],
                ['GST Number:', customer.get('gst_number', 'N/A')],
            ]
            pdf.add_modern_table(customer_info, col_widths=[1.5 * inch, 4 * inch], style='modern')
            
            # Customer Summary
            pdf.add_modern_section("Account Summary")
            pdf.add_modern_summary_card("Total Purchases", f"₹{customer.get('total_purchases', 0):.2f}", colors.HexColor('#2c5282'))
            pdf.add_modern_summary_card("Total Paid", f"₹{customer.get('total_paid', 0):.2f}", colors.HexColor('#38a169'))
            pdf.add_modern_summary_card("Outstanding Balance", f"₹{customer.get('outstanding_balance', 0):.2f}", 
                                      colors.HexColor('#e53e3e') if customer.get('outstanding_balance', 0) > 0 else colors.HexColor('#38a169'))
            pdf.add_modern_summary_card("Credit Limit", f"₹{customer.get('credit_limit', 0):.2f}", colors.HexColor('#3182ce'))
            
            pdf.elements.append(Spacer(1, 0.2 * inch))
            
            # Invoices
            invoices = customer.get('invoices', [])
            if invoices:
                pdf.add_modern_section(f"Invoices ({len(invoices)})")
                
                invoice_data = []
                for invoice in invoices:
                    invoice_data.append([
                        invoice.get('invoice_date', ''),
                        invoice.get('invoice_number', ''),
                        f"₹{invoice.get('total_amount', 0):.2f}",
                        f"₹{invoice.get('amount_paid', 0):.2f}",
                        f"₹{invoice.get('remaining_balance', 0):.2f}",
                        invoice.get('payment_status', '')
                    ])
                
                invoice_headers = ['Date', 'Invoice #', 'Total', 'Paid', 'Balance', 'Status']
                invoice_col_widths = [1 * inch, 1.2 * inch, 0.8 * inch, 0.7 * inch, 0.8 * inch, 0.8 * inch]
                pdf.add_modern_table(invoice_data, headers=invoice_headers, col_widths=invoice_col_widths, style='modern_right')
                
                # Invoice Items (show first few invoices in detail)
                for idx, invoice in enumerate(invoices[:3]):  # Show details for first 3 invoices
                    pdf.add_modern_section(f"Invoice Details: {invoice['invoice_number']}")
                    
                    items = invoice.get('items', [])
                    if items:
                        item_data = []
                        for item in items:
                            item_data.append([
                                item.get('product_name', ''),
                                str(item.get('quantity', 0)),
                                item.get('unit', ''),
                                f"₹{item.get('unit_price', 0):.2f}",
                                f"₹{item.get('gst_amount', 0):.2f}",
                                f"₹{item.get('line_total', 0):.2f}"
                            ])
                        
                        item_headers = ['Product', 'Qty', 'Unit', 'Price', 'GST', 'Total']
                        item_col_widths = [2 * inch, 0.5 * inch, 0.5 * inch, 0.7 * inch, 0.6 * inch, 0.7 * inch]
                        pdf.add_modern_table(item_data, headers=item_headers, col_widths=item_col_widths, style='modern_right')
            
            # Payments
            payments = customer.get('payments', [])
            if payments:
                pdf.add_modern_section(f"Payment History ({len(payments)})")
                
                payment_data = []
                for payment in payments:
                    payment_data.append([
                        payment.get('payment_date', ''),
                        payment.get('invoice_number', ''),
                        payment.get('payment_method', ''),
                        f"₹{payment.get('amount', 0):.2f}",
                        payment.get('reference_number', 'N/A')
                    ])
                
                payment_headers = ['Date', 'Invoice #', 'Method', 'Amount', 'Reference']
                payment_col_widths = [1 * inch, 1.2 * inch, 0.8 * inch, 0.8 * inch, 1 * inch]
                pdf.add_modern_table(payment_data, headers=payment_headers, col_widths=payment_col_widths, style='modern_right')
    
    # Footer
    pdf.add_modern_footer()
    
    return pdf.build()
