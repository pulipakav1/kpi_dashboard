-- forecasting queries
-- trying a few different approaches, not sure which one works best yet

-- historical revenue with moving averages
WITH monthly_revenue AS (
    SELECT 
        DATE_TRUNC('month', payment_date) AS month,
        SUM(amount) AS revenue,
        COUNT(DISTINCT customer_id) AS customers
    FROM payments
    WHERE payment_status = 'Success'
    GROUP BY DATE_TRUNC('month', payment_date)
)
SELECT 
    month,
    revenue,
    customers,
    AVG(revenue) OVER (
        ORDER BY month 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS revenue_3month_avg,
    AVG(revenue) OVER (
        ORDER BY month 
        ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
    ) AS revenue_6month_avg,
    LAG(revenue, 1) OVER (ORDER BY month) AS prev_month,
    LAG(revenue, 12) OVER (ORDER BY month) AS prev_year_same_month
FROM monthly_revenue
ORDER BY month DESC;

-- simple linear forecast for next 3 months
-- using average growth rate from last 6 months
WITH monthly_revenue AS (
    SELECT 
        DATE_TRUNC('month', payment_date) AS month,
        SUM(amount) AS revenue
    FROM payments
    WHERE payment_status = 'Success'
    GROUP BY DATE_TRUNC('month', payment_date)
),
revenue_with_trend AS (
    SELECT 
        month,
        revenue,
        ROW_NUMBER() OVER (ORDER BY month) AS month_num,
        AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS recent_avg,
        revenue - LAG(revenue, 1) OVER (ORDER BY month) AS month_over_month_change
    FROM monthly_revenue
),
trend_calculation AS (
    SELECT 
        AVG(month_over_month_change) AS avg_growth_rate
    FROM revenue_with_trend
    WHERE month_over_month_change IS NOT NULL
    ORDER BY month DESC
    LIMIT 6
)
SELECT 
    rwt.month AS historical_month,
    rwt.revenue AS historical_revenue,
    tc.avg_growth_rate,
    rwt.revenue + (tc.avg_growth_rate * 1) AS forecast_month_1,
    rwt.revenue + (tc.avg_growth_rate * 2) AS forecast_month_2,
    rwt.revenue + (tc.avg_growth_rate * 3) AS forecast_month_3
FROM revenue_with_trend rwt
CROSS JOIN trend_calculation tc
WHERE rwt.month = (SELECT MAX(month) FROM revenue_with_trend);

-- 6 month forecast using moving average
WITH monthly_revenue AS (
    SELECT 
        DATE_TRUNC('month', payment_date) AS month,
        SUM(amount) AS revenue
    FROM payments
    WHERE payment_status = 'Success'
    GROUP BY DATE_TRUNC('month', payment_date)
),
revenue_stats AS (
    SELECT 
        month,
        revenue,
        AVG(revenue) OVER (
            ORDER BY month 
            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
        ) AS ma_6month,
        AVG(revenue) OVER (
            ORDER BY month 
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS ma_3month
    FROM monthly_revenue
),
latest_stats AS (
    SELECT 
        month,
        revenue,
        ma_6month,
        ma_3month,
        (ma_3month - ma_6month) AS trend
    FROM revenue_stats
    WHERE month = (SELECT MAX(month) FROM revenue_stats)
)
SELECT 
    'Historical' AS period_type,
    ls.month AS period,
    ls.revenue AS value
FROM latest_stats ls
UNION ALL
SELECT 
    'Forecast' AS period_type,
    ls.month + (INTERVAL '1 month' * forecast_month) AS period,
    GREATEST(0, ls.ma_3month + (ls.trend * forecast_month)) AS value
FROM latest_stats ls
CROSS JOIN generate_series(1, 6) AS forecast_month
ORDER BY period_type DESC, period;

-- seasonal forecast based on year over year patterns
WITH monthly_revenue AS (
    SELECT 
        DATE_TRUNC('month', payment_date) AS month,
        EXTRACT(YEAR FROM payment_date) AS year,
        EXTRACT(MONTH FROM payment_date) AS month_num,
        SUM(amount) AS revenue
    FROM payments
    WHERE payment_status = 'Success'
    GROUP BY DATE_TRUNC('month', payment_date), 
             EXTRACT(YEAR FROM payment_date), 
             EXTRACT(MONTH FROM payment_date)
),
yoy_growth AS (
    SELECT 
        mr.month_num,
        AVG(
            CASE 
                WHEN prev.revenue > 0 
                THEN ((mr.revenue - prev.revenue)::DECIMAL / prev.revenue) * 100
                ELSE 0 
            END
        ) AS avg_yoy_growth_pct
    FROM monthly_revenue mr
    LEFT JOIN monthly_revenue prev 
        ON mr.month_num = prev.month_num 
        AND mr.year = prev.year + 1
    WHERE prev.revenue IS NOT NULL
    GROUP BY mr.month_num
),
latest_revenue AS (
    SELECT 
        month,
        month_num,
        year,
        revenue
    FROM monthly_revenue
    WHERE month = (SELECT MAX(month) FROM monthly_revenue)
),
forecast_months AS (
    SELECT 
        generate_series(1, 6) AS months_ahead,
        (EXTRACT(MONTH FROM lr.month) + generate_series(1, 6) - 1) % 12 + 1 AS forecast_month_num
    FROM latest_revenue lr
)
SELECT 
    lr.month + (INTERVAL '1 month' * fm.months_ahead) AS forecast_month,
    lr.revenue * POWER(1 + (yg.avg_yoy_growth_pct / 100), fm.months_ahead / 12.0) AS forecasted_revenue,
    yg.avg_yoy_growth_pct AS yoy_growth_rate
FROM latest_revenue lr
CROSS JOIN forecast_months fm
JOIN yoy_growth yg ON fm.forecast_month_num = yg.month_num
ORDER BY forecast_month;

-- combined forecast - using both methods
-- this is probably the most accurate
WITH monthly_revenue AS (
    SELECT 
        DATE_TRUNC('month', payment_date) AS month,
        SUM(amount) AS revenue
    FROM payments
    WHERE payment_status = 'Success'
    GROUP BY DATE_TRUNC('month', payment_date)
),
historical AS (
    SELECT 
        month,
        revenue,
        AVG(revenue) OVER (
            ORDER BY month 
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS ma_3month,
        AVG(revenue) OVER (
            ORDER BY month 
            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
        ) AS ma_6month
    FROM monthly_revenue
),
latest AS (
    SELECT 
        month,
        revenue,
        ma_3month,
        ma_6month,
        revenue - LAG(revenue, 1) OVER (ORDER BY month) AS mom_change,
        revenue - LAG(revenue, 12) OVER (ORDER BY month) AS yoy_change
    FROM historical
    WHERE month = (SELECT MAX(month) FROM historical)
),
forecast AS (
    SELECT 
        generate_series(1, 6) AS forecast_period,
        l.month + (INTERVAL '1 month' * generate_series(1, 6)) AS forecast_month,
        l.ma_3month AS method_ma,
        GREATEST(0, l.revenue + (l.mom_change * generate_series(1, 6))) AS method_linear,
        (l.ma_3month + GREATEST(0, l.revenue + (l.mom_change * generate_series(1, 6)))) / 2 AS method_combined
    FROM latest l
)
SELECT 
    'Historical' AS data_type,
    h.month AS period,
    h.revenue AS value,
    NULL AS forecast_method
FROM historical h
WHERE h.month >= (SELECT MAX(month) - INTERVAL '12 months' FROM historical)
UNION ALL
SELECT 
    'Forecast' AS data_type,
    f.forecast_month AS period,
    f.method_combined AS value,
    'Combined (MA + Linear)' AS forecast_method
FROM forecast f
ORDER BY data_type DESC, period;
