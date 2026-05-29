with payments as (
    select * from {{ ref('stg_payments') }}
),

monthly_agg as (
    select
        payment_month                                                       as month,
        sum(amount)                                                         as revenue,
        count(distinct customer_id)                                         as paying_customers,
        count(*)                                                            as successful_payments,
        avg(amount)                                                         as avg_payment_amount
    from payments
    where is_successful = true
    group by payment_month
),

with_growth as (
    select
        month,
        revenue,
        paying_customers,
        successful_payments,
        avg_payment_amount,
        lag(revenue) over (order by month)                                  as prev_month_revenue,
        lag(paying_customers) over (order by month)                         as prev_month_customers,
        round(
            (revenue - lag(revenue) over (order by month))
            / nullif(lag(revenue) over (order by month), 0) * 100,
            2
        )                                                                   as mom_revenue_growth_pct,
        round(
            (paying_customers - lag(paying_customers) over (order by month))
            / nullif(lag(paying_customers) over (order by month), 0) * 100,
            2
        )                                                                   as mom_customer_growth_pct,
        sum(revenue) over (order by month rows between unbounded preceding and current row)
                                                                            as cumulative_revenue
    from monthly_agg
)

select * from with_growth
order by month desc
