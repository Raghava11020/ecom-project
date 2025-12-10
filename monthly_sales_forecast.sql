-- Monthly Sales Trend Analysis and Forecasting
-- This query calculates monthly revenue, month-to-month changes, and trend analysis

WITH monthly_revenue AS (
    -- Calculate total revenue for each month
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
    -- Add previous month's revenue for comparison
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
    -- Calculate month-to-month changes and trends
    SELECT 
        month,
        year,
        month_num,
        total_revenue,
        order_count,
        previous_month_revenue,
        previous_month,
        -- Month-to-month change (absolute)
        total_revenue - COALESCE(previous_month_revenue, 0) AS revenue_change,
        -- Month-to-month percentage change
        CASE 
            WHEN previous_month_revenue > 0 
            THEN ROUND(((total_revenue - previous_month_revenue) / previous_month_revenue * 100), 2)
            ELSE NULL 
        END AS percent_change,
        -- Calculate cumulative average growth rate
        ROUND(AVG(total_revenue - COALESCE(previous_month_revenue, 0)) 
              OVER (ORDER BY year, month_num ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS avg_monthly_change
    FROM monthly_with_previous
)
SELECT 
    month,
    year,
    month_num,
    ROUND(total_revenue, 2) AS monthly_revenue,
    order_count,
    ROUND(COALESCE(previous_month_revenue, 0), 2) AS previous_month_revenue,
    ROUND(COALESCE(revenue_change, 0), 2) AS revenue_change,
    COALESCE(percent_change, 0) AS percent_change,
    -- Trend indicator
    CASE 
        WHEN revenue_change > 0 THEN '↑ Growing'
        WHEN revenue_change < 0 THEN '↓ Declining'
        WHEN revenue_change = 0 THEN '→ Stable'
        ELSE 'N/A'
    END AS trend,
    -- Simple forecast: next month = current month + average monthly change
    ROUND(total_revenue + COALESCE(avg_monthly_change, 0), 2) AS forecast_next_month,
    -- Calculate simple linear trend (slope) using linear regression approximation
    ROUND(
        (total_revenue - FIRST_VALUE(total_revenue) OVER (ORDER BY year, month_num)) / 
        NULLIF(ROW_NUMBER() OVER (ORDER BY year, month_num) - 1, 0), 
        2
    ) AS estimated_slope
FROM monthly_trends
ORDER BY year, month_num;

-- ============================================================================
-- ALTERNATIVE: Simplified version with linear regression for forecasting
-- ============================================================================

-- This query provides a cleaner view with linear trend calculation
WITH monthly_revenue AS (
    SELECT 
        strftime('%Y-%m', o.order_date) AS month,
        strftime('%Y', o.order_date) AS year,
        CAST(strftime('%m', o.order_date) AS INTEGER) AS month_num,
        SUM(oi.quantity * oi.price) AS total_revenue
    FROM orders o
    INNER JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY strftime('%Y-%m', o.order_date)
),
numbered_months AS (
    SELECT 
        month,
        year,
        month_num,
        total_revenue,
        ROW_NUMBER() OVER (ORDER BY year, month_num) AS month_sequence
    FROM monthly_revenue
),
trend_analysis AS (
    SELECT 
        month,
        year,
        month_num,
        total_revenue,
        month_sequence,
        LAG(total_revenue) OVER (ORDER BY month_sequence) AS prev_revenue,
        -- Calculate simple moving average of last 3 months for smoothing
        ROUND(AVG(total_revenue) OVER (
            ORDER BY month_sequence 
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 2) AS moving_avg_3months,
        -- Calculate overall average growth rate
        ROUND(AVG(total_revenue - LAG(total_revenue) OVER (ORDER BY month_sequence)) 
              OVER (), 2) AS avg_growth_rate
    FROM numbered_months
)
SELECT 
    month,
    ROUND(total_revenue, 2) AS monthly_revenue,
    ROUND(COALESCE(prev_revenue, 0), 2) AS previous_month,
    ROUND(total_revenue - COALESCE(prev_revenue, 0), 2) AS change_from_prev,
    ROUND(moving_avg_3months, 2) AS moving_avg_3mo,
    ROUND(avg_growth_rate, 2) AS avg_monthly_growth,
    -- Forecast: current revenue + average growth rate
    ROUND(total_revenue + avg_growth_rate, 2) AS forecast_next_month,
    -- Trend indicator
    CASE 
        WHEN (total_revenue - COALESCE(prev_revenue, 0)) > 0 THEN '↑'
        WHEN (total_revenue - COALESCE(prev_revenue, 0)) < 0 THEN '↓'
        ELSE '→'
    END AS trend
FROM trend_analysis
ORDER BY year, month_num;

