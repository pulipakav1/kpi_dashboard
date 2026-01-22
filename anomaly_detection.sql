-- anomaly detection queries
-- flagging unusual patterns in revenue, churn, etc

-- revenue anomalies - flagging months with >10-15% changes
WITH monthly_revenue AS (
    SELECT 
        DATE_TRUNC('month', payment_date) AS month,
        SUM(amount) AS revenue
    FROM payments
    WHERE payment_status = 'Success'
    GROUP BY DATE_TRUNC('month', payment_date)
),
revenue_with_stats AS (
    SELECT 
        month,
        revenue,
        LAG(revenue, 1) OVER (ORDER BY month) AS prev_month_revenue,
        AVG(revenue) OVER (
            ORDER BY month 
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
        ) AS avg_prev_6months,
        STDDEV(revenue) OVER (
            ORDER BY month 
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
        ) AS stddev_prev_6months
    FROM monthly_revenue
)
SELECT 
    month,
    revenue,
    prev_month_revenue,
    ROUND(
        ((revenue - prev_month_revenue)::DECIMAL / 
         NULLIF(prev_month_revenue, 0)) * 100, 
        2
    ) AS mom_change_pct,
    avg_prev_6months,
    CASE 
        WHEN ABS((revenue - prev_month_revenue)::DECIMAL / NULLIF(prev_month_revenue, 0)) > 0.15 
        THEN 'HIGH ANOMALY (>15% change)'
        WHEN ABS((revenue - prev_month_revenue)::DECIMAL / NULLIF(prev_month_revenue, 0)) > 0.10 
        THEN 'MEDIUM ANOMALY (>10% change)'
        ELSE 'Normal'
    END AS anomaly_flag,
    CASE 
        WHEN revenue < (avg_prev_6months - 2 * COALESCE(stddev_prev_6months, 0))
        THEN 'Statistical Outlier (2+ std devs below mean)'
        WHEN revenue > (avg_prev_6months + 2 * COALESCE(stddev_prev_6months, 0))
        THEN 'Statistical Outlier (2+ std devs above mean)'
        ELSE NULL
    END AS statistical_anomaly
FROM revenue_with_stats
WHERE prev_month_revenue IS NOT NULL
ORDER BY month DESC;

-- churn spike detection
WITH monthly_churn AS (
    SELECT 
        DATE_TRUNC('month', end_date) AS month,
        COUNT(DISTINCT customer_id) AS churned_customers
    FROM subscriptions
    WHERE end_date IS NOT NULL
    GROUP BY DATE_TRUNC('month', end_date)
),
churn_with_stats AS (
    SELECT 
        month,
        churned_customers,
        LAG(churned_customers, 1) OVER (ORDER BY month) AS prev_month_churn,
        AVG(churned_customers) OVER (
            ORDER BY month 
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
        ) AS avg_prev_6months,
        STDDEV(churned_customers) OVER (
            ORDER BY month 
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
        ) AS stddev_prev_6months
    FROM monthly_churn
)
SELECT 
    month,
    churned_customers,
    prev_month_churn,
    ROUND(
        ((churned_customers - prev_month_churn)::DECIMAL / 
         NULLIF(prev_month_churn, 0)) * 100, 
        2
    ) AS churn_increase_pct,
    CASE 
        WHEN churned_customers > (avg_prev_6months + 2 * COALESCE(stddev_prev_6months, 0))
        THEN 'CHURN SPIKE DETECTED'
        WHEN churned_customers > (avg_prev_6months + 1.5 * COALESCE(stddev_prev_6months, 0))
        THEN 'Elevated Churn'
        ELSE 'Normal'
    END AS anomaly_flag
FROM churn_with_stats
WHERE prev_month_churn IS NOT NULL
ORDER BY month DESC;

-- churn spike by segment
WITH segment_churn AS (
    SELECT 
        c.segment,
        DATE_TRUNC('month', s.end_date) AS month,
        COUNT(DISTINCT s.customer_id) AS churned_customers
    FROM subscriptions s
    JOIN customers c ON s.customer_id = c.customer_id
    WHERE s.end_date IS NOT NULL
    GROUP BY c.segment, DATE_TRUNC('month', s.end_date)
),
segment_stats AS (
    SELECT 
        segment,
        month,
        churned_customers,
        AVG(churned_customers) OVER (
            PARTITION BY segment
            ORDER BY month 
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
        ) AS avg_prev_6months,
        STDDEV(churned_customers) OVER (
            PARTITION BY segment
            ORDER BY month 
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
        ) AS stddev_prev_6months
    FROM segment_churn
)
SELECT 
    segment,
    month,
    churned_customers,
    ROUND(avg_prev_6months, 0) AS avg_prev_6months,
    CASE 
        WHEN churned_customers > (avg_prev_6months + 2 * COALESCE(stddev_prev_6months, 0))
        THEN 'SPIKE: ' || ROUND(
            ((churned_customers - avg_prev_6months)::DECIMAL / 
             NULLIF(avg_prev_6months, 0)) * 100, 
            1
        ) || '% above average'
        ELSE 'Normal'
    END AS anomaly_status
FROM segment_stats
WHERE avg_prev_6months IS NOT NULL
ORDER BY month DESC, churned_customers DESC;

-- conversion drop detection
WITH monthly_conversions AS (
    SELECT 
        DATE_TRUNC('month', c.signup_date) AS month,
        COUNT(DISTINCT c.customer_id) AS total_signups,
        COUNT(DISTINCT s.customer_id) AS converted_customers,
        ROUND(
            (COUNT(DISTINCT s.customer_id)::DECIMAL / 
             NULLIF(COUNT(DISTINCT c.customer_id), 0)) * 100, 
            2
        ) AS conversion_rate_pct
    FROM customers c
    LEFT JOIN subscriptions s ON c.customer_id = s.customer_id
    GROUP BY DATE_TRUNC('month', c.signup_date)
),
conversion_stats AS (
    SELECT 
        month,
        conversion_rate_pct,
        LAG(conversion_rate_pct, 1) OVER (ORDER BY month) AS prev_month_rate,
        AVG(conversion_rate_pct) OVER (
            ORDER BY month 
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
        ) AS avg_prev_6months,
        STDDEV(conversion_rate_pct) OVER (
            ORDER BY month 
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
        ) AS stddev_prev_6months
    FROM monthly_conversions
)
SELECT 
    month,
    conversion_rate_pct,
    prev_month_rate,
    ROUND(conversion_rate_pct - prev_month_rate, 2) AS rate_change,
    CASE 
        WHEN conversion_rate_pct < (avg_prev_6months - 2 * COALESCE(stddev_prev_6months, 0))
        THEN 'CONVERSION DROP: Significant decrease detected'
        WHEN conversion_rate_pct < (avg_prev_6months - 1.5 * COALESCE(stddev_prev_6months, 0))
        THEN 'CONVERSION DROP: Moderate decrease'
        WHEN conversion_rate_pct < prev_month_rate - 5
        THEN 'CONVERSION DROP: >5% MoM decrease'
        ELSE 'Normal'
    END AS anomaly_flag
FROM conversion_stats
WHERE prev_month_rate IS NOT NULL
ORDER BY month DESC;

-- comprehensive anomaly report - all in one
WITH revenue_anomalies AS (
    SELECT 
        DATE_TRUNC('month', payment_date) AS month,
        SUM(amount) AS revenue,
        LAG(SUM(amount), 1) OVER (ORDER BY DATE_TRUNC('month', payment_date)) AS prev_revenue
    FROM payments
    WHERE payment_status = 'Success'
    GROUP BY DATE_TRUNC('month', payment_date)
),
churn_anomalies AS (
    SELECT 
        DATE_TRUNC('month', end_date) AS month,
        COUNT(DISTINCT customer_id) AS churned
    FROM subscriptions
    WHERE end_date IS NOT NULL
    GROUP BY DATE_TRUNC('month', end_date)
),
conversion_anomalies AS (
    SELECT 
        DATE_TRUNC('month', c.signup_date) AS month,
        COUNT(DISTINCT c.customer_id) AS signups,
        COUNT(DISTINCT s.customer_id) AS conversions
    FROM customers c
    LEFT JOIN subscriptions s ON c.customer_id = s.customer_id
    GROUP BY DATE_TRUNC('month', c.signup_date)
)
SELECT 
    COALESCE(ra.month, ca.month, conv.month) AS month,
    ra.revenue,
    CASE 
        WHEN ABS((ra.revenue - ra.prev_revenue)::DECIMAL / NULLIF(ra.prev_revenue, 0)) > 0.15
        THEN 'Revenue anomaly (>15% change)'
        WHEN ABS((ra.revenue - ra.prev_revenue)::DECIMAL / NULLIF(ra.prev_revenue, 0)) > 0.10
        THEN 'Revenue anomaly (>10% change)'
        ELSE NULL
    END AS revenue_anomaly,
    ca.churned,
    CASE 
        WHEN ca.churned > (SELECT AVG(churned) * 1.5 FROM churn_anomalies WHERE month < ca.month)
        THEN 'Churn spike detected'
        ELSE NULL
    END AS churn_anomaly,
    ROUND((conv.conversions::DECIMAL / NULLIF(conv.signups, 0)) * 100, 2) AS conversion_rate,
    CASE 
        WHEN (conv.conversions::DECIMAL / NULLIF(conv.signups, 0)) < 
             (SELECT AVG(conversions::DECIMAL / NULLIF(signups, 0)) * 0.85 
              FROM conversion_anomalies WHERE month < conv.month)
        THEN 'Conversion drop detected'
        ELSE NULL
    END AS conversion_anomaly
FROM revenue_anomalies ra
FULL OUTER JOIN churn_anomalies ca ON ra.month = ca.month
FULL OUTER JOIN conversion_anomalies conv ON COALESCE(ra.month, ca.month) = conv.month
WHERE COALESCE(ra.month, ca.month, conv.month) >= 
      (SELECT MAX(COALESCE(ra.month, ca.month, conv.month)) - INTERVAL '12 months' 
       FROM revenue_anomalies ra
       FULL OUTER JOIN churn_anomalies ca ON ra.month = ca.month
       FULL OUTER JOIN conversion_anomalies conv ON COALESCE(ra.month, ca.month) = conv.month)
ORDER BY month DESC;

-- revenue and churn correlation
-- trying to see if revenue drops correlate with churn spikes
WITH revenue_churn_correlation AS (
    SELECT 
        DATE_TRUNC('month', p.payment_date) AS revenue_month,
        SUM(p.amount) AS revenue,
        LAG(SUM(p.amount), 1) OVER (ORDER BY DATE_TRUNC('month', p.payment_date)) AS prev_revenue
    FROM payments p
    WHERE p.payment_status = 'Success'
    GROUP BY DATE_TRUNC('month', p.payment_date)
),
churn_by_segment_month AS (
    SELECT 
        c.segment,
        DATE_TRUNC('month', s.end_date) AS churn_month,
        COUNT(DISTINCT s.customer_id) AS churned
    FROM subscriptions s
    JOIN customers c ON s.customer_id = c.customer_id
    WHERE s.end_date IS NOT NULL
    GROUP BY c.segment, DATE_TRUNC('month', s.end_date)
)
SELECT 
    rc.revenue_month AS month,
    rc.revenue,
    ROUND(((rc.revenue - rc.prev_revenue)::DECIMAL / NULLIF(rc.prev_revenue, 0)) * 100, 2) AS revenue_change_pct,
    cbs.segment,
    cbs.churned AS segment_churn,
    CASE 
        WHEN ABS((rc.revenue - rc.prev_revenue)::DECIMAL / NULLIF(rc.prev_revenue, 0)) > 0.12 
             AND cbs.churned > (SELECT AVG(churned) * 1.3 
                                FROM churn_by_segment_month 
                                WHERE segment = cbs.segment 
                                AND churn_month < cbs.churn_month)
        THEN 'Revenue dropped ' || 
             ROUND(ABS((rc.revenue - rc.prev_revenue)::DECIMAL / NULLIF(rc.prev_revenue, 0)) * 100, 1) || 
             '% in ' || TO_CHAR(rc.revenue_month, 'Month YYYY') || 
             ' due to ' || ROUND(((cbs.churned::DECIMAL / 
                                   NULLIF((SELECT AVG(churned) 
                                           FROM churn_by_segment_month 
                                           WHERE segment = cbs.segment 
                                           AND churn_month < cbs.churn_month), 0)) - 1) * 100, 1) || 
             '% increase in churn among ' || cbs.segment || ' customers.'
        ELSE NULL
    END AS insight
FROM revenue_churn_correlation rc
JOIN churn_by_segment_month cbs ON rc.revenue_month = cbs.churn_month
WHERE ABS((rc.revenue - rc.prev_revenue)::DECIMAL / NULLIF(rc.prev_revenue, 0)) > 0.10
ORDER BY rc.revenue_month DESC, cbs.churned DESC;
