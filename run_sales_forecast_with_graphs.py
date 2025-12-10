"""
Run Monthly Sales Trend Analysis and Forecasting with Visualizations
Includes graphs showing monthly revenue, trends, and forecasts
"""

import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np

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

# Prepare data for visualization
months = []
revenues = []
changes = []
percent_changes = []
orders = []

for row in results:
    month, revenue, order_count, prev_rev, change, pct_change, trend = row
    months.append(month)
    revenues.append(revenue)
    changes.append(change)
    percent_changes.append(pct_change)
    orders.append(order_count)
    print(f"{month:<10} ${revenue:<14.2f} {order_count:<8} ${prev_rev:<11.2f} ${change:<11.2f} {pct_change:<9.2f}% {trend:<12}")

print()

# Calculate average growth rate for forecasting
revenue_changes = [c for c in changes if c != 0]
avg_growth = sum(revenue_changes) / len(revenue_changes) if revenue_changes else 0
last_month_revenue = revenues[-1] if revenues else 0

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

# Calculate overall trend
if results:
    first_revenue = results[0][1]
    last_revenue = results[-1][1]
    num_months = len(results)
    slope = (last_revenue - first_revenue) / (num_months - 1) if num_months > 1 else 0
    avg_revenue = sum(row[1] for row in results) / len(results)
    
    print("\n" + "="*80)
    print("OVERALL TREND ANALYSIS")
    print("="*80)
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

forecast_months = []
forecast_revenues = []

for i in range(1, 4):
    forecast_revenue = last_month_revenue + (avg_growth * i)
    forecast_months.append(f"Forecast {i}")
    forecast_revenues.append(forecast_revenue)
    print(f"Forecast Month {i}: ${forecast_revenue:,.2f}")

# Create visualizations
print("\n" + "="*80)
print("Generating visualizations...")
print("="*80)

# Convert month strings to datetime for plotting
month_dates = [datetime.strptime(m, '%Y-%m') for m in months]

# Create figure with subplots - increased spacing
fig = plt.figure(figsize=(18, 12))
fig.suptitle('Monthly Sales Trend Analysis and Forecasting', fontsize=18, fontweight='bold', y=0.995)

# Use gridspec for better control over spacing
gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.3, left=0.08, right=0.95, top=0.93, bottom=0.08)

# Plot 1: Monthly Revenue Over Time
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(month_dates, revenues, marker='o', linewidth=2.5, markersize=7, color='#2E86AB', label='Monthly Revenue', zorder=3)
ax1.axhline(y=avg_revenue, color='r', linestyle='--', linewidth=2, label=f'Average: ${avg_revenue:,.0f}', zorder=2)
ax1.fill_between(month_dates, revenues, alpha=0.2, color='#2E86AB', zorder=1)
ax1.set_title('Monthly Revenue Over Time', fontsize=14, fontweight='bold', pad=15)
ax1.set_xlabel('Month', fontsize=11, fontweight='bold')
ax1.set_ylabel('Revenue ($)', fontsize=11, fontweight='bold')
ax1.legend(loc='best', fontsize=10, framealpha=0.9)
ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=9)
plt.setp(ax1.yaxis.get_majorticklabels(), fontsize=9)

# Plot 2: Month-to-Month Change
ax2 = fig.add_subplot(gs[0, 1])
colors = ['#28a745' if c > 0 else '#dc3545' if c < 0 else '#6c757d' for c in changes]
bars = ax2.bar(month_dates, changes, color=colors, alpha=0.8, width=25, edgecolor='black', linewidth=0.5)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=1.2, zorder=1)
ax2.axhline(y=avg_growth, color='blue', linestyle='--', linewidth=2, label=f'Avg Change: ${avg_growth:,.0f}', zorder=2)
ax2.set_title('Month-to-Month Revenue Change', fontsize=14, fontweight='bold', pad=15)
ax2.set_xlabel('Month', fontsize=11, fontweight='bold')
ax2.set_ylabel('Revenue Change ($)', fontsize=11, fontweight='bold')
ax2.legend(loc='best', fontsize=10, framealpha=0.9)
ax2.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=0.8)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=9)
plt.setp(ax2.yaxis.get_majorticklabels(), fontsize=9)

# Plot 3: Trend Line with Forecast
ax3 = fig.add_subplot(gs[1, 0])
# Historical data
ax3.plot(month_dates, revenues, marker='o', linewidth=2.5, markersize=7, color='#2E86AB', label='Historical Revenue', zorder=3)

# Calculate and plot trend line
if len(month_dates) > 1:
    x_numeric = np.arange(len(month_dates))
    z = np.polyfit(x_numeric, revenues, 1)
    p = np.poly1d(z)
    trend_line = p(x_numeric)
    ax3.plot(month_dates, trend_line, '--', color='orange', linewidth=2.5, label='Trend Line', alpha=0.8, zorder=2)

# Forecast data
forecast_start_date = month_dates[-1]
forecast_dates = []
for i in range(1, 4):
    # Add months to the last date
    if forecast_start_date.month == 12:
        forecast_date = datetime(forecast_start_date.year + 1, 1, 1)
    else:
        forecast_date = datetime(forecast_start_date.year, forecast_start_date.month + i, 1)
    forecast_dates.append(forecast_date)

# Plot forecast
forecast_all_dates = [month_dates[-1]] + forecast_dates
forecast_all_revenues = [revenues[-1]] + forecast_revenues
ax3.plot(forecast_all_dates, forecast_all_revenues, marker='s', linewidth=2.5, markersize=9, 
         color='#28a745', linestyle=':', label='Forecast (Next 3 Months)', alpha=0.9, zorder=4)

# Add vertical line to separate historical from forecast
ax3.axvline(x=month_dates[-1], color='gray', linestyle=':', linewidth=1.5, alpha=0.7, zorder=1)

ax3.set_title('Revenue Trend with Forecast', fontsize=14, fontweight='bold', pad=15)
ax3.set_xlabel('Month', fontsize=11, fontweight='bold')
ax3.set_ylabel('Revenue ($)', fontsize=11, fontweight='bold')
ax3.legend(loc='best', fontsize=10, framealpha=0.9)
ax3.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=9)
plt.setp(ax3.yaxis.get_majorticklabels(), fontsize=9)

# Plot 4: Percentage Change
ax4 = fig.add_subplot(gs[1, 1])
colors_pct = ['#28a745' if p > 0 else '#dc3545' if p < 0 else '#6c757d' for p in percent_changes]
bars_pct = ax4.bar(month_dates, percent_changes, color=colors_pct, alpha=0.8, width=25, edgecolor='black', linewidth=0.5)
ax4.axhline(y=0, color='black', linestyle='-', linewidth=1.2, zorder=1)
ax4.set_title('Month-to-Month Percentage Change', fontsize=14, fontweight='bold', pad=15)
ax4.set_xlabel('Month', fontsize=11, fontweight='bold')
ax4.set_ylabel('Percentage Change (%)', fontsize=11, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=0.8)
ax4.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax4.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=9)
plt.setp(ax4.yaxis.get_majorticklabels(), fontsize=9)

# Save the figure
output_file = 'sales_forecast_analysis.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\nGraphs saved to: {output_file}")

# Try to display the plot (may not work in all environments)
try:
    plt.show()
except:
    print("Note: Interactive display not available. Check the saved PNG file.")

conn.close()

print("\n" + "="*80)
print("Analysis Complete!")
print("="*80)

