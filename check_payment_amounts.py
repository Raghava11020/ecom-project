"""
Check if payment amounts match order totals
Compares payment.amount with sum(order_items.quantity * order_items.price) for each order
"""

import sqlite3

# Connect to database
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

print("="*70)
print("PAYMENT AMOUNT vs ORDER TOTAL COMPARISON")
print("="*70)
print()

# Query to calculate order totals and compare with payment amounts
query = """
SELECT 
    o.order_id,
    o.order_date,
    o.status,
    COALESCE(SUM(oi.quantity * oi.price), 0) AS order_total,
    p.amount AS payment_amount,
    CASE 
        WHEN ABS(COALESCE(SUM(oi.quantity * oi.price), 0) - p.amount) < 0.01 
        THEN 'MATCH' 
        ELSE 'MISMATCH' 
    END AS status_check,
    ABS(COALESCE(SUM(oi.quantity * oi.price), 0) - p.amount) AS difference
FROM orders o
LEFT JOIN order_items oi ON o.order_id = oi.order_id
LEFT JOIN payments p ON o.order_id = p.order_id
GROUP BY o.order_id, o.order_date, o.status, p.amount
ORDER BY o.order_id
"""

cursor.execute(query)
results = cursor.fetchall()

# Statistics
total_orders = len(results)
matching = sum(1 for row in results if row[5] == 'MATCH')
mismatching = total_orders - matching

print(f"Total Orders: {total_orders}")
print(f"Matching: {matching} ({matching/total_orders*100:.1f}%)")
print(f"Mismatching: {mismatching} ({mismatching/total_orders*100:.1f}%)")
print()
print("="*70)
print("DETAILED RESULTS")
print("="*70)
print()

# Display results
print(f"{'Order ID':<10} {'Order Total':<15} {'Payment Amount':<15} {'Status':<10} {'Difference':<12}")
print("-" * 70)

for row in results:
    order_id, order_date, status, order_total, payment_amount, status_check, difference = row
    order_total = order_total if order_total else 0
    payment_amount = payment_amount if payment_amount else 0
    
    print(f"{order_id:<10} ${order_total:<14.2f} ${payment_amount:<14.2f} {status_check:<10} ${difference:<11.2f}")

print()
print("="*70)

# Show mismatches in detail
if mismatching > 0:
    print("\nMISMATCHES DETAIL:")
    print("="*70)
    print(f"{'Order ID':<10} {'Order Total':<15} {'Payment Amount':<15} {'Difference':<12}")
    print("-" * 70)
    
    for row in results:
        order_id, order_date, status, order_total, payment_amount, status_check, difference = row
        if status_check == 'MISMATCH':
            order_total = order_total if order_total else 0
            payment_amount = payment_amount if payment_amount else 0
            print(f"{order_id:<10} ${order_total:<14.2f} ${payment_amount:<14.2f} ${difference:<11.2f}")

# Check for orders without payments
print("\n" + "="*70)
print("ORDERS WITHOUT PAYMENTS:")
print("="*70)

cursor.execute("""
    SELECT o.order_id, COALESCE(SUM(oi.quantity * oi.price), 0) AS order_total
    FROM orders o
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    LEFT JOIN payments p ON o.order_id = p.order_id
    WHERE p.payment_id IS NULL
    GROUP BY o.order_id
""")

no_payment = cursor.fetchall()
if no_payment:
    print(f"{'Order ID':<10} {'Order Total':<15}")
    print("-" * 30)
    for row in no_payment:
        print(f"{row[0]:<10} ${row[1]:<14.2f}")
    print(f"\nTotal orders without payments: {len(no_payment)}")
else:
    print("All orders have payments.")

# Check for payments without orders
print("\n" + "="*70)
print("PAYMENTS WITHOUT ORDERS:")
print("="*70)

cursor.execute("""
    SELECT p.payment_id, p.order_id, p.amount
    FROM payments p
    LEFT JOIN orders o ON p.order_id = o.order_id
    WHERE o.order_id IS NULL
""")

orphan_payments = cursor.fetchall()
if orphan_payments:
    print(f"{'Payment ID':<12} {'Order ID':<10} {'Amount':<15}")
    print("-" * 40)
    for row in orphan_payments:
        print(f"{row[0]:<12} {row[1]:<10} ${row[2]:<14.2f}")
    print(f"\nTotal orphan payments: {len(orphan_payments)}")
else:
    print("All payments are linked to orders.")

conn.close()

print("\n" + "="*70)
print("Analysis complete!")
print("="*70)

