with subscriptions as (
    select * from {{ ref('stg_subscriptions') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

monthly_active as (
    select
        date_trunc('month', start_date)                 as month,
        count(distinct customer_id)                     as active_subscriptions
    from subscriptions
    where is_active = true
    group by date_trunc('month', start_date)
),

monthly_churned as (
    select
        date_trunc('month', end_date)                   as month,
        segment,
        count(distinct s.customer_id)                   as churned_customers
    from subscriptions s
    join customers c using (customer_id)
    where end_date is not null
    group by date_trunc('month', end_date), segment
),

segment_totals as (
    select
        date_trunc('month', end_date)                   as month,
        segment,
        count(distinct s.customer_id)                   as churned_customers,
        count(distinct case when s.end_date is null then s.customer_id end)
                                                        as retained_customers
    from subscriptions s
    join customers c using (customer_id)
    group by date_trunc('month', end_date), segment
),

overall_churn as (
    select
        coalesce(ma.month, mc.month)                    as month,
        coalesce(ma.active_subscriptions, 0)            as active_subscriptions,
        coalesce(sum(mc.churned_customers), 0)          as churned_customers,
        round(
            coalesce(sum(mc.churned_customers), 0)::numeric
            / nullif(coalesce(ma.active_subscriptions, 0)
                     + coalesce(sum(mc.churned_customers), 0), 0) * 100,
            2
        )                                               as churn_rate_pct
    from monthly_active ma
    full outer join monthly_churned mc on ma.month = mc.month
    group by coalesce(ma.month, mc.month), ma.active_subscriptions
)

select
    month,
    active_subscriptions,
    churned_customers,
    churn_rate_pct,
    lag(churn_rate_pct) over (order by month)           as prev_month_churn_rate_pct,
    round(
        churn_rate_pct - lag(churn_rate_pct) over (order by month),
        2
    )                                                   as churn_rate_delta_pct
from overall_churn
order by month desc
