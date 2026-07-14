#!/usr/bin/env python3
"""
Add transport_charges column to invoices table
"""
import sqlite3
import os

db_path = 'data/billing.db'

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if column already exists
    cursor.execute("PRAGMA table_info(invoice)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'transport_charges' in columns:
        print("Column 'transport_charges' already exists in invoice table")
    else:
        # Add the column
        cursor.execute("ALTER TABLE invoice ADD COLUMN transport_charges NUMERIC(12,2) DEFAULT 0")
        conn.commit()
        print("Successfully added 'transport_charges' column to invoice table")
        
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
