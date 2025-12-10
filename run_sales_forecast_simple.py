"""
Run Monthly Sales Trend Analysis and Forecasting (Simple version - no pandas)
Executes SQL queries and displays results in a readable format
"""

import sqlite3

# Connect to database
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

print("="*80)
print("MONTHLY SALES TREND ANALYSIS AND FORECASTING")
print("="*80)
print()

# Query: Monthly revenue with trends
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
),
monthly_with_previous AS (
    SELECT 
        month,
        year,
        month_num,
        total_revenue,
        order_count,
        LAG(total_revenue) OVER (ORDER BY year, month_num) AS previous_month_revenue
    FROM monthly_revenue
),
monthly_trends AS (
    SELECT 
        month,
        year,
        month_num,
        total_revenue,
        order_count,
        previous_month_revenue,
        total_revenue - COALESCE(previous_month_revenue, 0) AS revenue_change,
        CASE 
            WHEN previous_month_revenue > 0 
            THEN ROUND(((total_revenue - previous_month_revenue) * 100.0 / previous_month_revenue), 2)
            ELSE NULL 
        END AS percent_change,
        ROUND(AVG(total_revenue - COALESCE(previous_month_revenue, 0)) 
              OVER (ORDER BY year, month_num ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS avg_monthly_change
    FROM monthly_with_previous
)
SELECT 
    month,
    ROUND(total_revenue, 2) AS monthly_revenue,
    order_count,
    ROUND(COALESCE(previous_month_revenue, 0), 2) AS previous_month_revenue,
    ROUND(COALESCE(revenue_change, 0), 2) AS revenue_change,
    COALESCE(percent_change, 0) AS percent_change,
    CASE 
        WHEN revenue_change > 0 THEN '↑ Growing'
        WHEN revenue_change < 0 THEN '↓ Declining'
        WHEN revenue_change = 0 THEN '→ Stable'
        ELSE 'N/A'
    END AS trend,
    ROUND(total_revenue + COALESCE(avg_monthly_change, 0), 2) AS forecast_next_month
FROM monthly_trends
ORDER BY year, month_num;
"""

print("MONTHLY REVENUE TREND ANALYSIS")
print("-" * 80)
print(f"{'Month':<10} {'Revenue':<15} {'Orders':<8} {'Prev Month':<12} {'Change':<12} {'% Change':<10} {'Trend':<12} {'Forecast':<12}")
print("-" * 80)

cursor.execute(query)
results = cursor.fetchall()

for row in results:
    month, revenue, orders, prev_rev, change, pct_change, trend, forecast = row
    print(f"{month:<10} ${revenue:<14.2f} {orders:<8} ${prev_rev:<11.2f} ${change:<11.2f} {pct_change:<9.2f}% {trend:<12} ${forecast:<11.2f}")

print()

# Summary statistics
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

summary_query = """
WITH monthly_revenue AS (
    SELECT 
        strftime('%Y-%m', o.order_date) AS month,
        strftime('%Y', o.order_date) AS year,
        strftime('%m', o.order_date) AS month_num,
        SUM(oi.quantity * oi.price) AS total_revenue
    FROM orders o
    INNER JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY strftime('%Y-%m', o.order_date)
),
monthly_trends AS (
    SELECT 
        total_revenue,
        total_revenue - LAG(total_revenue) OVER (ORDER BY year, month_num) AS revenue_change,
        CASE 
            WHEN LAG(total_revenue) OVER (ORDER BY year, month_num) > 0 
            THEN ((total_revenue - LAG(total_revenue) OVER (ORDER BY year, month_num)) / 
                  LAG(total_revenue) OVER (ORDER BY year, month_num) * 100)
            ELSE NULL 
        END AS percent_change
    FROM monthly_revenue
)
SELECT 
    COUNT(*) AS total_months,
    ROUND(SUM(total_revenue), 2) AS total_revenue,
    ROUND(AVG(total_revenue), 2) AS avg_monthly_revenue,
    ROUND(MIN(total_revenue), 2) AS min_monthly_revenue,
    ROUND(MAX(total_revenue), 2) AS max_monthly_revenue,
    ROUND(AVG(revenue_change), 2) AS avg_monthly_change,
    ROUND(AVG(percent_change), 2) AS avg_percent_change
FROM monthly_trends
WHERE revenue_change IS NOT NULL;
"""

cursor.execute(summary_query)
summary = cursor.fetchone()

if summary:
    print(f"Total Months Analyzed: {summary[0]}")
    print(f"Total Revenue: ${summary[1]:,.2f}")
    print(f"Average Monthly Revenue: ${summary[2]:,.2f}")
    print(f"Minimum Monthly Revenue: ${summary[3]:,.2f}")
    print(f"Maximum Monthly Revenue: ${summary[4]:,.2f}")
    print(f"Average Monthly Change: ${summary[5]:,.2f}")
    print(f"Average % Change: {summary[6]:.2f}%")

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
    ROUND(AVG(total_revenue), 2) AS avg_monthly_revenue,
    CASE 
        WHEN (MAX(total_revenue) - MIN(total_revenue)) / NULLIF(MAX(month_sequence) - MIN(month_sequence), 0) > 0 
        THEN 'Positive Trend (Growing)'
        WHEN (MAX(total_revenue) - MIN(total_revenue)) / NULLIF(MAX(month_sequence) - MIN(month_sequence), 0) < 0 
        THEN 'Negative Trend (Declining)'
        ELSE 'Stable'
    END AS trend_direction
FROM monthly_revenue;
"""

cursor.execute(trend_query)
trend = cursor.fetchone()

if trend:
    print(f"Overall Slope (Trend): ${trend[0]:,.2f} per month")
    print(f"Average Monthly Revenue: ${trend[1]:,.2f}")
    print(f"Trend Direction: {trend[2]}")

# Forecast
print("\n" + "="*80)
print("SALES FORECAST (Next 3 Months)")
print("="*80)

forecast_query = """
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
),
trend_calc AS (
    SELECT 
        AVG(total_revenue - LAG(total_revenue) OVER (ORDER BY month_sequence)) AS avg_growth_rate,
        MAX(total_revenue) AS last_month_revenue
    FROM monthly_revenue
)
SELECT 
    'Forecast Month 1' AS forecast_period,
    ROUND(last_month_revenue + avg_growth_rate, 2) AS forecasted_revenue
FROM trend_calc
UNION ALL
SELECT 
    'Forecast Month 2',
    ROUND(last_month_revenue + (avg_growth_rate * 2), 2)
FROM trend_calc
UNION ALL
SELECT 
    'Forecast Month 3',
    ROUND(last_month_revenue + (avg_growth_rate * 3), 2)
FROM trend_calc;
"""

cursor.execute(forecast_query)
forecasts = cursor.fetchall()

print(f"{'Period':<20} {'Forecasted Revenue':<20}")
print("-" * 40)
for period, revenue in forecasts:
    print(f"{period:<20} ${revenue:<19,.2f}")

conn.close()

print("\n" + "="*80)
print("Analysis Complete!")
print("="*80)

