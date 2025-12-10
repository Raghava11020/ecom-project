"""
Run Monthly Sales Trend Analysis and Forecasting (Compatible version)
Works with older SQLite versions - no window functions
"""

import sqlite3

# Connect to database
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

print("="*80)
print("MONTHLY SALES TREND ANALYSIS AND FORECASTING")
print("="*80)
print()

# Query: Monthly revenue with trends (using self-join instead of window functions)
query = """
WITH monthly_revenue AS (
    SELECT 
        strftime('%Y-%m', o.order_date) AS month,
        strftime('%Y', o.order_date) AS year,
        CAST(strftime('%m', o.order_date) AS INTEGER) AS month_num,
        SUM(oi.quantity * oi.price) AS total_revenue,
        COUNT(DISTINCT o.order_id) AS order_count
    FROM orders o
    INNER JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY strftime('%Y-%m', o.order_date)
)
SELECT 
    m1.month,
    ROUND(m1.total_revenue, 2) AS monthly_revenue,
    m1.order_count,
    ROUND(COALESCE(m2.total_revenue, 0), 2) AS previous_month_revenue,
    ROUND(m1.total_revenue - COALESCE(m2.total_revenue, 0), 2) AS revenue_change,
    CASE 
        WHEN m2.total_revenue > 0 
        THEN ROUND(((m1.total_revenue - m2.total_revenue) * 100.0 / m2.total_revenue), 2)
        ELSE 0
    END AS percent_change,
    CASE 
        WHEN (m1.total_revenue - COALESCE(m2.total_revenue, 0)) > 0 THEN '↑ Growing'
        WHEN (m1.total_revenue - COALESCE(m2.total_revenue, 0)) < 0 THEN '↓ Declining'
        ELSE '→ Stable'
    END AS trend
FROM monthly_revenue m1
LEFT JOIN monthly_revenue m2 ON (
    (m2.year = m1.year AND m2.month_num = m1.month_num - 1) OR
    (m2.year = m1.year - 1 AND m1.month_num = 1 AND m2.month_num = 12)
)
ORDER BY m1.year, m1.month_num;
"""

print("MONTHLY REVENUE TREND ANALYSIS")
print("-" * 80)
print(f"{'Month':<10} {'Revenue':<15} {'Orders':<8} {'Prev Month':<12} {'Change':<12} {'% Change':<10} {'Trend':<12}")
print("-" * 80)

cursor.execute(query)
results = cursor.fetchall()

# Calculate average monthly change for forecasting
revenue_changes = []
for row in results:
    month, revenue, orders, prev_rev, change, pct_change, trend = row
    print(f"{month:<10} ${revenue:<14.2f} {orders:<8} ${prev_rev:<11.2f} ${change:<11.2f} {pct_change:<9.2f}% {trend:<12}")
    if change is not None and change != 0:
        revenue_changes.append(change)

print()

# Calculate average growth rate
avg_growth = sum(revenue_changes) / len(revenue_changes) if revenue_changes else 0
last_month_revenue = results[-1][1] if results else 0

# Summary statistics
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

summary_query = """
SELECT 
    COUNT(*) AS total_months,
    ROUND(SUM(total_revenue), 2) AS total_revenue,
    ROUND(AVG(total_revenue), 2) AS avg_monthly_revenue,
    ROUND(MIN(total_revenue), 2) AS min_monthly_revenue,
    ROUND(MAX(total_revenue), 2) AS max_monthly_revenue
FROM (
    SELECT 
        strftime('%Y-%m', o.order_date) AS month,
        SUM(oi.quantity * oi.price) AS total_revenue
    FROM orders o
    INNER JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY strftime('%Y-%m', o.order_date)
);
"""

cursor.execute(summary_query)
summary = cursor.fetchone()

if summary:
    print(f"Total Months Analyzed: {summary[0]}")
    print(f"Total Revenue: ${summary[1]:,.2f}")
    print(f"Average Monthly Revenue: ${summary[2]:,.2f}")
    print(f"Minimum Monthly Revenue: ${summary[3]:,.2f}")
    print(f"Maximum Monthly Revenue: ${summary[4]:,.2f}")
    print(f"Average Monthly Change: ${avg_growth:,.2f}")

# Overall trend
print("\n" + "="*80)
print("OVERALL TREND ANALYSIS")
print("="*80)

trend_query = """
WITH monthly_revenue AS (
    SELECT 
        strftime('%Y-%m', o.order_date) AS month,
        strftime('%Y', o.order_date) AS year,
        CAST(strftime('%m', o.order_date) AS INTEGER) AS month_num,
        SUM(oi.quantity * oi.price) AS total_revenue,
        ROW_NUMBER() OVER (ORDER BY year, month_num) AS month_sequence
    FROM orders o
    INNER JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY strftime('%Y-%m', o.order_date)
)
SELECT 
    ROUND(
        (MAX(total_revenue) - MIN(total_revenue)) / 
        NULLIF(MAX(month_sequence) - MIN(month_sequence), 0), 
        2
    ) AS overall_slope,
    ROUND(AVG(total_revenue), 2) AS avg_monthly_revenue
FROM monthly_revenue;
"""

try:
    cursor.execute(trend_query)
    trend = cursor.fetchone()
    if trend:
        print(f"Overall Slope (Trend): ${trend[0]:,.2f} per month")
        print(f"Average Monthly Revenue: ${trend[1]:,.2f}")
        if trend[0] > 0:
            print("Trend Direction: Positive Trend (Growing)")
        elif trend[0] < 0:
            print("Trend Direction: Negative Trend (Declining)")
        else:
            print("Trend Direction: Stable")
except:
    # Fallback if window functions not supported
    if results:
        first_revenue = results[0][1]
        last_revenue = results[-1][1]
        num_months = len(results)
        slope = (last_revenue - first_revenue) / (num_months - 1) if num_months > 1 else 0
        avg_revenue = sum(row[1] for row in results) / len(results)
        print(f"Overall Slope (Trend): ${slope:,.2f} per month")
        print(f"Average Monthly Revenue: ${avg_revenue:,.2f}")
        if slope > 0:
            print("Trend Direction: Positive Trend (Growing)")
        elif slope < 0:
            print("Trend Direction: Negative Trend (Declining)")
        else:
            print("Trend Direction: Stable")

# Forecast
print("\n" + "="*80)
print("SALES FORECAST (Next 3 Months)")
print("="*80)

print(f"{'Period':<20} {'Forecasted Revenue':<20}")
print("-" * 40)
print(f"{'Forecast Month 1':<20} ${last_month_revenue + avg_growth:<19,.2f}")
print(f"{'Forecast Month 2':<20} ${last_month_revenue + (avg_growth * 2):<19,.2f}")
print(f"{'Forecast Month 3':<20} ${last_month_revenue + (avg_growth * 3):<19,.2f}")

conn.close()

print("\n" + "="*80)
print("Analysis Complete!")
print("="*80)

