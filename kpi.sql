-- KPI queries for dashboard
-- started working on these after getting the data loaded

-- monthly revenue - basic one to start
SELECT 
    DATE_TRUNC('month', payment_date) AS month,
    SUM(amount) AS monthly_revenue,
    COUNT(DISTINCT customer_id) AS paying_customers,
    COUNT(*) AS total_payments
FROM payments
WHERE payment_status = 'Success'
GROUP BY DATE_TRUNC('month', payment_date)
ORDER BY month DESC;

-- revenue breakdown by segment
SELECT 
    c.segment,
    DATE_TRUNC('month', p.payment_date) AS month,
    SUM(p.amount) AS segment_revenue,
    COUNT(DISTINCT p.customer_id) AS customers
FROM payments p
JOIN customers c ON p.customer_id = c.customer_id
WHERE p.payment_status = 'Success'
GROUP BY c.segment, DATE_TRUNC('month', p.payment_date)
ORDER BY month DESC, segment;

-- revenue by plan type
SELECT 
    s.plan_type,
    DATE_TRUNC('month', p.payment_date) AS month,
    SUM(p.amount) AS plan_revenue,
    COUNT(DISTINCT p.customer_id) AS customers
FROM payments p
JOIN subscriptions s ON p.customer_id = s.customer_id
WHERE p.payment_status = 'Success'
GROUP BY s.plan_type, DATE_TRUNC('month', p.payment_date)
ORDER BY month DESC, plan_revenue DESC;

-- churn rate calculation
-- formula: churned / total customers * 100
-- had to think about this one for a bit
WITH monthly_customers AS (
    SELECT 
        DATE_TRUNC('month', start_date) AS month,
        COUNT(DISTINCT customer_id) AS new_customers
    FROM subscriptions
    GROUP BY DATE_TRUNC('month', start_date)
),
monthly_churned AS (
    SELECT 
        DATE_TRUNC('month', end_date) AS month,
        COUNT(DISTINCT customer_id) AS churned_customers
    FROM subscriptions
    WHERE end_date IS NOT NULL
    GROUP BY DATE_TRUNC('month', end_date)
),
monthly_active AS (
    SELECT 
        DATE_TRUNC('month', payment_date) AS month,
        COUNT(DISTINCT customer_id) AS active_customers
    FROM payments
    WHERE payment_status = 'Success'
    GROUP BY DATE_TRUNC('month', payment_date)
)
SELECT 
    COALESCE(mc.month, ma.month) AS month,
    COALESCE(ma.active_customers, 0) AS active_customers,
    COALESCE(mch.churned_customers, 0) AS churned_customers,
    CASE 
        WHEN COALESCE(ma.active_customers, 0) > 0 
        THEN ROUND((COALESCE(mch.churned_customers, 0)::DECIMAL / 
                   (COALESCE(ma.active_customers, 0) + COALESCE(mch.churned_customers, 0))) * 100, 2)
        ELSE 0 
    END AS churn_rate_pct
FROM monthly_active ma
FULL OUTER JOIN monthly_churned mch ON ma.month = mch.month
FULL OUTER JOIN monthly_customers mc ON COALESCE(ma.month, mch.month) = mc.month
ORDER BY month DESC;

-- churn by segment - this one was tricky
SELECT 
    c.segment,
    DATE_TRUNC('month', s.end_date) AS month,
    COUNT(DISTINCT s.customer_id) AS churned_customers,
    COUNT(DISTINCT CASE WHEN s.end_date IS NULL THEN s.customer_id END) AS active_customers,
    ROUND(
        (COUNT(DISTINCT s.customer_id)::DECIMAL / 
         NULLIF(COUNT(DISTINCT s.customer_id) + 
                COUNT(DISTINCT CASE WHEN s.end_date IS NULL THEN s.customer_id END), 0)) * 100, 
        2
    ) AS churn_rate_pct
FROM subscriptions s
JOIN customers c ON s.customer_id = c.customer_id
WHERE s.end_date IS NOT NULL
GROUP BY c.segment, DATE_TRUNC('month', s.end_date)
ORDER BY month DESC, churn_rate_pct DESC;

-- retention rate
-- (customers at end - new) / customers at start
WITH monthly_start AS (
    SELECT 
        DATE_TRUNC('month', payment_date) AS month,
        COUNT(DISTINCT customer_id) AS customers_at_start
    FROM payments
    WHERE payment_status = 'Success'
    GROUP BY DATE_TRUNC('month', payment_date)
),
monthly_new AS (
    SELECT 
        DATE_TRUNC('month', start_date) AS month,
        COUNT(DISTINCT customer_id) AS new_customers
    FROM subscriptions
    GROUP BY DATE_TRUNC('month', start_date)
),
monthly_end AS (
    SELECT 
        DATE_TRUNC('month', payment_date) AS month,
        COUNT(DISTINCT customer_id) AS customers_at_end
    FROM payments
    WHERE payment_status = 'Success'
    GROUP BY DATE_TRUNC('month', payment_date)
)
SELECT 
    ms.month,
    ms.customers_at_start,
    COALESCE(mn.new_customers, 0) AS new_customers,
    me.customers_at_end,
    CASE 
        WHEN ms.customers_at_start > 0 
        THEN ROUND(
            ((me.customers_at_end - COALESCE(mn.new_customers, 0))::DECIMAL / 
             ms.customers_at_start) * 100, 
            2
        )
        ELSE 0 
    END AS retention_rate_pct
FROM monthly_start ms
JOIN monthly_end me ON ms.month = me.month
LEFT JOIN monthly_new mn ON ms.month = mn.month
ORDER BY ms.month DESC;

-- conversion rate
-- assuming signup = trial start, might need to adjust
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
ORDER BY month DESC;

-- conversion by channel
SELECT 
    c.acquisition_channel,
    COUNT(DISTINCT c.customer_id) AS total_signups,
    COUNT(DISTINCT s.customer_id) AS converted_customers,
    ROUND(
        (COUNT(DISTINCT s.customer_id)::DECIMAL / 
         NULLIF(COUNT(DISTINCT c.customer_id), 0)) * 100, 
        2
    ) AS conversion_rate_pct
FROM customers c
LEFT JOIN subscriptions s ON c.customer_id = s.customer_id
GROUP BY c.acquisition_channel
ORDER BY conversion_rate_pct DESC;

-- month over month growth
WITH monthly_revenue AS (
    SELECT 
        DATE_TRUNC('month', payment_date) AS month,
        SUM(amount) AS revenue
    FROM payments
    WHERE payment_status = 'Success'
    GROUP BY DATE_TRUNC('month', payment_date)
)
SELECT 
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS previous_month_revenue,
    revenue - LAG(revenue) OVER (ORDER BY month) AS revenue_change,
    ROUND(
        ((revenue - LAG(revenue) OVER (ORDER BY month))::DECIMAL / 
         NULLIF(LAG(revenue) OVER (ORDER BY month), 0)) * 100, 
        2
    ) AS mom_growth_pct
FROM monthly_revenue
ORDER BY month DESC;

-- customer count mom growth
WITH monthly_customers AS (
    SELECT 
        DATE_TRUNC('month', payment_date) AS month,
        COUNT(DISTINCT customer_id) AS customer_count
    FROM payments
    WHERE payment_status = 'Success'
    GROUP BY DATE_TRUNC('month', payment_date)
)
SELECT 
    month,
    customer_count,
    LAG(customer_count) OVER (ORDER BY month) AS previous_month_customers,
    customer_count - LAG(customer_count) OVER (ORDER BY month) AS customer_change,
    ROUND(
        ((customer_count - LAG(customer_count) OVER (ORDER BY month))::DECIMAL / 
         NULLIF(LAG(customer_count) OVER (ORDER BY month), 0)) * 100, 
        2
    ) AS mom_growth_pct
FROM monthly_customers
ORDER BY month DESC;

-- year over year
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
)
SELECT 
    mr.month,
    mr.revenue AS current_revenue,
    prev.revenue AS previous_year_revenue,
    mr.revenue - prev.revenue AS revenue_change,
    ROUND(
        ((mr.revenue - prev.revenue)::DECIMAL / 
         NULLIF(prev.revenue, 0)) * 100, 
        2
    ) AS yoy_growth_pct
FROM monthly_revenue mr
LEFT JOIN monthly_revenue prev 
    ON mr.month_num = prev.month_num 
    AND mr.year = prev.year + 1
ORDER BY mr.month DESC;

-- gross margin calculation
-- revenue - costs / revenue
SELECT 
    c.month,
    COALESCE(SUM(p.amount), 0) AS revenue,
    (c.infra_cost + c.marketing_cost + c.support_cost) AS total_costs,
    COALESCE(SUM(p.amount), 0) - (c.infra_cost + c.marketing_cost + c.support_cost) AS gross_profit,
    ROUND(
        ((COALESCE(SUM(p.amount), 0) - (c.infra_cost + c.marketing_cost + c.support_cost))::DECIMAL / 
         NULLIF(COALESCE(SUM(p.amount), 0), 0)) * 100, 
        2
    ) AS gross_margin_pct
FROM costs c
LEFT JOIN payments p 
    ON DATE_TRUNC('month', p.payment_date) = TO_DATE(c.month || '-01', 'YYYY-MM-DD')
    AND p.payment_status = 'Success'
GROUP BY c.month, c.infra_cost, c.marketing_cost, c.support_cost
ORDER BY c.month DESC;

-- cost vs revenue trend
SELECT 
    c.month,
    COALESCE(SUM(p.amount), 0) AS revenue,
    c.infra_cost,
    c.marketing_cost,
    c.support_cost,
    (c.infra_cost + c.marketing_cost + c.support_cost) AS total_costs,
    COALESCE(SUM(p.amount), 0) - (c.infra_cost + c.marketing_cost + c.support_cost) AS net_profit
FROM costs c
LEFT JOIN payments p 
    ON DATE_TRUNC('month', p.payment_date) = TO_DATE(c.month || '-01', 'YYYY-MM-DD')
    AND p.payment_status = 'Success'
GROUP BY c.month, c.infra_cost, c.marketing_cost, c.support_cost
ORDER BY c.month DESC;

-- customer lifetime value by segment
SELECT 
    c.segment,
    COUNT(DISTINCT c.customer_id) AS total_customers,
    SUM(p.amount) AS total_revenue,
    ROUND(AVG(customer_ltv.total_revenue), 2) AS avg_ltv
FROM customers c
JOIN (
    SELECT 
        customer_id,
        SUM(amount) AS total_revenue
    FROM payments
    WHERE payment_status = 'Success'
    GROUP BY customer_id
) customer_ltv ON c.customer_id = customer_ltv.customer_id
JOIN payments p ON c.customer_id = p.customer_id
WHERE p.payment_status = 'Success'
GROUP BY c.segment
ORDER BY avg_ltv DESC;

-- executive summary - quick overview
WITH latest_month AS (
    SELECT MAX(DATE_TRUNC('month', payment_date)) AS month
    FROM payments
    WHERE payment_status = 'Success'
),
monthly_metrics AS (
    SELECT 
        DATE_TRUNC('month', p.payment_date) AS month,
        SUM(p.amount) AS revenue,
        COUNT(DISTINCT p.customer_id) AS active_customers
    FROM payments p
    WHERE p.payment_status = 'Success'
    GROUP BY DATE_TRUNC('month', p.payment_date)
),
churn_metrics AS (
    SELECT 
        DATE_TRUNC('month', s.end_date) AS month,
        COUNT(DISTINCT s.customer_id) AS churned
    FROM subscriptions s
    WHERE s.end_date IS NOT NULL
    GROUP BY DATE_TRUNC('month', s.end_date)
)
SELECT 
    lm.month,
    mm.revenue,
    mm.active_customers,
    COALESCE(cm.churned, 0) AS churned_customers,
    CASE 
        WHEN mm.active_customers > 0 
        THEN ROUND((COALESCE(cm.churned, 0)::DECIMAL / mm.active_customers) * 100, 2)
        ELSE 0 
    END AS churn_rate_pct
FROM latest_month lm
JOIN monthly_metrics mm ON lm.month = mm.month
LEFT JOIN churn_metrics cm ON lm.month = cm.month;
