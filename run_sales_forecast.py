"""
Run Monthly Sales Trend Analysis and Forecasting
Executes SQL queries and displays results in a readable format
"""

import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('ecommerce.db')

print("="*80)
print("MONTHLY SALES TREND ANALYSIS AND FORECASTING")
print("="*80)
print()

# Query 1: Detailed monthly revenue with trends
query1 = """
WITH monthly_revenue AS (
    SELECT 
        strftime('%Y-%m', o.order_date) AS month,
        strftime('%Y', o.order_date) AS year,
        strftime('%m', o.order_date) AS month_num,
        SUM(oi.quantity * oi.price) AS total_revenue,
        COUNT(DISTINCT o.order_id) AS order_count
    FROM orders o
    INNER JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY strftime('%Y-%m', o.order_date)
    ORDER BY year, month_num
),
monthly_with_previous AS (
    SELECT 
        month,
        year,
        month_num,
        total_revenue,
        order_count,
        LAG(total_revenue) OVER (ORDER BY year, month_num) AS previous_month_revenue,
        LAG(month) OVER (ORDER BY year, month_num) AS previous_month
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
        previous_month,
        total_revenue - COALESCE(previous_month_revenue, 0) AS revenue_change,
        CASE 
            WHEN previous_month_revenue > 0 
            THEN ROUND(((total_revenue - previous_month_revenue) / previous_month_revenue * 100), 2)
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
df1 = pd.read_sql_query(query1, conn)
print(df1.to_string(index=False))
print()

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
    ROUND(MAX(total_revenue), 2) AS max_monthly_revenue,
    ROUND(AVG(revenue_change), 2) AS avg_monthly_change,
    ROUND(AVG(percent_change), 2) AS avg_percent_change
FROM (
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
            month,
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
    SELECT * FROM monthly_trends WHERE revenue_change IS NOT NULL
);
"""

df_summary = pd.read_sql_query(summary_query, conn)
print(df_summary.to_string(index=False))
print()

# Calculate overall trend (slope)
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

df_trend = pd.read_sql_query(trend_query, conn)
print(df_trend.to_string(index=False))
print()

# Forecast for next 3 months
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
        MAX(total_revenue) AS last_month_revenue,
        MAX(month_sequence) AS last_month_seq
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

df_forecast = pd.read_sql_query(forecast_query, conn)
print(df_forecast.to_string(index=False))
print()

conn.close()

print("\n" + "="*80)
print("Analysis Complete!")
print("="*80)

