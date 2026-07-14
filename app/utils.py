from datetime import datetime
from sqlalchemy import func
from app.models import db, Invoice, Product, Customer
import re

def generate_invoice_number():
    """Generate unique invoice number in VSA-XXXX format"""
    # Get the highest invoice number overall (not per day)
    prefix = "VSA-"
    latest_invoice = Invoice.query.filter(
        Invoice.invoice_number.like(f'{prefix}%')
    ).order_by(Invoice.invoice_number.desc()).first()
    
    if latest_invoice:
        # Extract the number part and increment
        try:
            last_num = int(latest_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1
    
    return f"{prefix}{str(new_num).zfill(4)}"

def generate_product_code():
    """Generate compact unique product code like PRD-001, PRD-002, ...

    This function is robust to older product codes with different formats
    by extracting the trailing numeric sequence if present.
    """
    prefix = "PRD-"
    latest_product = Product.query.filter(
        Product.product_code.like(f'{prefix}%')
    ).order_by(Product.id.desc()).first()

    if latest_product and latest_product.product_code:
        # Try to extract trailing digits (e.g., PRD-001 or PRD-20260616...-3)
        m = re.search(r'(\d+)$', latest_product.product_code)
        if m:
            try:
                last_num = int(m.group(1))
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            # Fallback: get max numeric suffix across all PRD- codes
            codes = [p.product_code for p in Product.query.filter(Product.product_code.like(f'{prefix}%')).all() if p.product_code]
            max_n = 0
            for c in codes:
                m2 = re.search(r'(\d+)$', c)
                if m2:
                    try:
                        n = int(m2.group(1))
                        if n > max_n:
                            max_n = n
                    except ValueError:
                        continue
            new_num = max_n + 1
    else:
        new_num = 1

    return f"{prefix}{str(new_num).zfill(3)}"

def generate_customer_code():
    """Generate unique customer code"""
    prefix = "CUST-"
    latest_customer = Customer.query.filter(
        Customer.customer_code.like(f'{prefix}%')
    ).order_by(Customer.customer_code.desc()).first()
    
    if latest_customer:
        try:
            last_num = int(latest_customer.customer_code.split('-')[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1
    
    return f"{prefix}{str(new_num).zfill(5)}"


def amount_in_words(amount):
    """Convert amount to words (Indian numbering system)"""
    try:
        num = float(amount)
        if num == 0:
            return "Zero Rupees Only"
        
        # Split into integer and decimal parts
        integer_part = int(num)
        decimal_part = int(round((num - integer_part) * 100))
        
        def convert_less_than_thousand(n):
            if n == 0:
                return ""
            elif n < 20:
                ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
                       "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
                return ones[n]
            elif n < 100:
                tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
                return tens[n // 10] + (" " + convert_less_than_thousand(n % 10) if n % 10 != 0 else "")
            else:
                hundreds = n // 100
                remainder = n % 100
                ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
                result = ones[hundreds] + " Hundred"
                if remainder != 0:
                    result += " " + convert_less_than_thousand(remainder)
                return result
        
        def convert_chunk(n):
            if n == 0:
                return ""
            elif n < 1000:
                return convert_less_than_thousand(n)
            elif n < 100000:
                thousands = n // 1000
                remainder = n % 1000
                result = convert_less_than_thousand(thousands) + " Thousand"
                if remainder != 0:
                    result += " " + convert_chunk(remainder)
                return result
            elif n < 10000000:
                lakhs = n // 100000
                remainder = n % 100000
                result = convert_less_than_thousand(lakhs) + " Lakh"
                if remainder != 0:
                    result += " " + convert_chunk(remainder)
                return result
            else:
                crores = n // 10000000
                remainder = n % 10000000
                result = convert_less_than_thousand(crores) + " Crore"
                if remainder != 0:
                    result += " " + convert_chunk(remainder)
                return result
        
        words = convert_chunk(integer_part)
        
        if decimal_part > 0:
            words += " and " + convert_less_than_thousand(decimal_part) + " Paise"
        
        return words + " Only"
    except:
        return str(amount)
