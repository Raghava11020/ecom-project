"""
E-commerce Data Generator
Generates sample CSV files for customers, products, orders, order_items, and payments
"""

import csv
import random
from datetime import datetime, timedelta
from faker import Faker

# Initialize Faker for generating realistic data
fake = Faker()

# Configuration
NUM_CUSTOMERS = 100
NUM_PRODUCTS = 50
NUM_ORDERS = 200
MIN_ITEMS_PER_ORDER = 1
MAX_ITEMS_PER_ORDER = 5
PAYMENT_METHODS = ['UPI', 'Card', 'Wallet', 'Net Banking', 'Cash on Delivery']
ORDER_STATUSES = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']

# Generate customers.csv
print("Generating customers.csv...")
customers = []
for i in range(1, NUM_CUSTOMERS + 1):
    country = fake.country()
    customers.append({
        'customer_id': i,
        'customer_name': fake.name(),
        'email': fake.email(),
        'phone number': fake.phone_number(),
        'city': fake.city(),
        'country': country
    })

with open('customers.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['customer_id', 'customer_name', 'email', 'phone number', 'city', 'country'])
    writer.writeheader()
    writer.writerows(customers)

# Generate products.csv
print("Generating products.csv...")
categories = ['Electronics', 'Clothing', 'Books', 'Home & Kitchen', 'Sports', 'Toys', 'Beauty', 'Food']
products = []
for i in range(1, NUM_PRODUCTS + 1):
    products.append({
        'product_id': i,
        'product_name': fake.catch_phrase(),
        'category': random.choice(categories),
        'price': round(random.uniform(10.0, 1000.0), 2)
    })

with open('products.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['product_id', 'product_name', 'category', 'price'])
    writer.writeheader()
    writer.writerows(products)

# Generate orders.csv
print("Generating orders.csv...")
orders = []
start_date = datetime(2006, 1, 1)
end_date = datetime(2007, 12, 31)
for i in range(1, NUM_ORDERS + 1):
    order_date = fake.date_between(start_date=start_date, end_date=end_date)
    orders.append({
        'order_id': i,
        'customer_id': random.randint(1, NUM_CUSTOMERS),
        'order_date': order_date.strftime('%m/%d/%Y'),
        'status': random.choice(ORDER_STATUSES)
    })

with open('orders.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['order_id', 'customer_id', 'order_date', 'status'])
    writer.writeheader()
    writer.writerows(orders)

# Generate order_items.csv
print("Generating order_items.csv...")
order_items = []
item_id = 1
product_prices = {p['product_id']: p['price'] for p in products}

for order in orders:
    num_items = random.randint(MIN_ITEMS_PER_ORDER, MAX_ITEMS_PER_ORDER)
    order_products = random.sample(range(1, NUM_PRODUCTS + 1), min(num_items, NUM_PRODUCTS))
    
    for product_id in order_products:
        quantity = random.randint(1, 5)
        # Price at time of order (may vary slightly from current price)
        base_price = product_prices[product_id]
        price_at_order = round(base_price * random.uniform(0.9, 1.1), 2)
        
        order_items.append({
            'item_id': item_id,
            'order_id': order['order_id'],
            'product_id': product_id,
            'quantity': quantity,
            'price': price_at_order
        })
        item_id += 1

with open('order_items.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['item_id', 'order_id', 'product_id', 'quantity', 'price'])
    writer.writeheader()
    writer.writerows(order_items)

# Generate payments.csv
print("Generating payments.csv...")
payments = []
payment_id = 1

# Calculate order totals from order_items
order_totals = {}
for item in order_items:
    order_id = item['order_id']
    total = item['quantity'] * item['price']
    order_totals[order_id] = order_totals.get(order_id, 0) + total

for order in orders:
    order_id = order['order_id']
    amount = round(order_totals.get(order_id, random.uniform(50.0, 500.0)), 2)
    
    # Payment date should be on or after order date, but still within 2006-2007 range
    order_date = datetime.strptime(order['order_date'], '%m/%d/%Y')
    days_after_order = random.randint(0, 7)
    payment_date = order_date + timedelta(days=days_after_order)
    # Ensure payment_date doesn't exceed end_date
    if payment_date > end_date:
        payment_date = end_date
    
    payments.append({
        'payment_id': payment_id,
        'amount': amount,
        'order_id': order_id,
        'payment_method': random.choice(PAYMENT_METHODS),
        'payment_date': payment_date.strftime('%m/%d/%Y')
    })
    payment_id += 1

with open('payments.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['payment_id', 'amount', 'order_id', 'payment_method', 'payment_date'])
    writer.writeheader()
    writer.writerows(payments)

print("\nAll CSV files generated successfully!")
print(f"- customers.csv: {NUM_CUSTOMERS} records")
print(f"- products.csv: {NUM_PRODUCTS} records")
print(f"- orders.csv: {NUM_ORDERS} records")
print(f"- order_items.csv: {len(order_items)} records")
print(f"- payments.csv: {len(payments)} records")

