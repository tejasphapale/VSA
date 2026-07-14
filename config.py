"""
Configuration file for Shop Billing Software
Modify these settings to customize your application
"""

# ============== FLASK CONFIGURATION ==============
DEBUG = False  # Set to False in production
SECRET_KEY = 'your-secret-key-change-in-production-use-random-32-characters'

# ============== DATABASE ==============
DATABASE_PATH = 'data/billing.db'
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'

# ============== APPLICATION ==============
APP_NAME = 'Shop Billing Software'
APP_VERSION = '1.0.0'
APP_TIMEZONE = 'Asia/Kolkata'

# ============== CURRENCY ==============
CURRENCY_SYMBOL = '₹'
CURRENCY_CODE = 'INR'
DECIMAL_PLACES = 2

# ============== INVOICE ==============
INVOICE_PREFIX = 'INV'
INVOICE_DATE_FORMAT = '%d/%m/%Y'
DEFAULT_PAYMENT_METHOD = 'Cash'
DEFAULT_GST_RATE = 18  # Default GST percentage

# ============== PRODUCT ==============
PRODUCT_CODE_PREFIX = 'PRD'
DEFAULT_PRODUCT_UNIT = 'Piece'
LOW_STOCK_ALERT = True
LOW_STOCK_THRESHOLD = 10

# ============== CUSTOMER ==============
CUSTOMER_CODE_PREFIX = 'CUST'
ALLOW_CREDIT_SALES = True
DEFAULT_CREDIT_LIMIT = 0

# ============== PAGINATION ==============
INVOICES_PER_PAGE = 20
PRODUCTS_PER_PAGE = 50
CUSTOMERS_PER_PAGE = 50

# ============== EMAIL (FOR FUTURE USE) ==============
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-app-password'

# ============== REPORT ==============
REPORT_DATE_FORMAT = '%d %B %Y'
INCLUDE_TAX_IN_REPORTS = True

# ============== UI CUSTOMIZATION ==============
PRIMARY_COLOR = '#1976d2'
SECONDARY_COLOR = '#7b1fa2'
SUCCESS_COLOR = '#388e3c'
WARNING_COLOR = '#f57c00'
DANGER_COLOR = '#d32f2f'

# ============== SESSION ==============
PERMANENT_SESSION_LIFETIME = 3600  # 1 hour in seconds
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS

# ============== BACKUP ==============
AUTO_BACKUP = False
BACKUP_FREQUENCY = 'weekly'  # daily, weekly, monthly

# ============== ADVANCED ==============
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_FILE_EXTENSIONS = ['pdf', 'txt', 'csv']
ENABLE_API = True
API_RATE_LIMIT = 1000  # Requests per hour

# ============== FEATURES ==============
FEATURES = {
    'invoicing': True,
    'inventory': True,
    'customers': True,
    'reports': True,
    'payments': True,
    'expenses': True,
    'categories': True,
}

# Payment Methods
PAYMENT_METHODS = ['Cash', 'Card', 'UPI', 'Cheque', 'Credit']

# Product Units
PRODUCT_UNITS = ['Piece', 'kg', 'liter', 'meter', 'box', 'pack', 'dozen']

# Invoice Status
INVOICE_STATUS = ['Draft', 'Finalized', 'Cancelled']

# Payment Status
PAYMENT_STATUS = ['Paid', 'Unpaid', 'Partial']

# Expense Categories
EXPENSE_CATEGORIES = [
    'Rent',
    'Electricity',
    'Water',
    'Transport',
    'Staff Salary',
    'Maintenance',
    'Office Supplies',
    'Insurance',
    'Marketing',
    'Other'
]
