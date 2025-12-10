"""
SQLite Data Ingestion Script
Reads CSV files and imports them into a SQLite database
"""

import csv
import sqlite3
from datetime import datetime

# Database file name
DB_FILE = 'ecommerce.db'

# Create connection to SQLite database
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

print("Creating database schema...")

# Create customers table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY,
        customer_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone_number TEXT,
        city TEXT,
        country TEXT
    )
''')

# Create products table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT,
        price REAL NOT NULL
    )
''')

# Create orders table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        order_date DATE NOT NULL,
        status TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    )
''')

# Create order_items table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        item_id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
''')

# Create payments table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        payment_id INTEGER PRIMARY KEY,
        amount REAL NOT NULL,
        order_id INTEGER NOT NULL,
        payment_method TEXT,
        payment_date DATE NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    )
''')

print("Schema created successfully!")
print("\nImporting data from CSV files...")

# Import customers.csv
print("Importing customers.csv...")
with open('customers.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    customers_data = []
    for row in reader:
        customers_data.append((
            int(row['customer_id']),
            row['customer_name'],
            row['email'],
            row['phone number'],
            row['city'],
            row['country']
        ))
    cursor.executemany('''
        INSERT OR REPLACE INTO customers 
        (customer_id, customer_name, email, phone_number, city, country)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', customers_data)
    print(f"  Imported {len(customers_data)} customers")

# Import products.csv
print("Importing products.csv...")
with open('products.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    products_data = []
    for row in reader:
        products_data.append((
            int(row['product_id']),
            row['product_name'],
            row['category'],
            float(row['price'])
        ))
    cursor.executemany('''
        INSERT OR REPLACE INTO products 
        (product_id, product_name, category, price)
        VALUES (?, ?, ?, ?)
    ''', products_data)
    print(f"  Imported {len(products_data)} products")

# Import orders.csv
print("Importing orders.csv...")
with open('orders.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    orders_data = []
    for row in reader:
        # Parse date from MM/DD/YYYY format
        order_date_str = row['order_date']
        try:
            # Try MM/DD/YYYY format first
            order_date = datetime.strptime(order_date_str, '%m/%d/%Y').date()
        except ValueError:
            # Fallback to YYYY-MM-DD format
            order_date = datetime.strptime(order_date_str, '%Y-%m-%d').date()
        
        orders_data.append((
            int(row['order_id']),
            int(row['customer_id']),
            order_date.isoformat(),
            row['status']
        ))
    cursor.executemany('''
        INSERT OR REPLACE INTO orders 
        (order_id, customer_id, order_date, status)
        VALUES (?, ?, ?, ?)
    ''', orders_data)
    print(f"  Imported {len(orders_data)} orders")

# Import order_items.csv
print("Importing order_items.csv...")
with open('order_items.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    order_items_data = []
    for row in reader:
        order_items_data.append((
            int(row['item_id']),
            int(row['order_id']),
            int(row['product_id']),
            int(row['quantity']),
            float(row['price'])
        ))
    cursor.executemany('''
        INSERT OR REPLACE INTO order_items 
        (item_id, order_id, product_id, quantity, price)
        VALUES (?, ?, ?, ?, ?)
    ''', order_items_data)
    print(f"  Imported {len(order_items_data)} order items")

# Import payments.csv
print("Importing payments.csv...")
with open('payments.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    payments_data = []
    for row in reader:
        # Parse date from MM/DD/YYYY format
        payment_date_str = row['payment_date']
        try:
            # Try MM/DD/YYYY format first
            payment_date = datetime.strptime(payment_date_str, '%m/%d/%Y').date()
        except ValueError:
            # Fallback to YYYY-MM-DD format
            payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
        
        payments_data.append((
            int(row['payment_id']),
            float(row['amount']),
            int(row['order_id']),
            row['payment_method'],
            payment_date.isoformat()
        ))
    cursor.executemany('''
        INSERT OR REPLACE INTO payments 
        (payment_id, amount, order_id, payment_method, payment_date)
        VALUES (?, ?, ?, ?, ?)
    ''', payments_data)
    print(f"  Imported {len(payments_data)} payments")

# Commit all changes
conn.commit()

# Display summary
print("\n" + "="*50)
print("Data import completed successfully!")
print("="*50)

# Show record counts
cursor.execute("SELECT COUNT(*) FROM customers")
print(f"Customers: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM products")
print(f"Products: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM orders")
print(f"Orders: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM order_items")
print(f"Order Items: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM payments")
print(f"Payments: {cursor.fetchone()[0]}")

# Close connection
conn.close()

print(f"\nDatabase saved to: {DB_FILE}")

