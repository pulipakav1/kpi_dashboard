with revenue as (
    select
        month,
        revenue
    from {{ ref('fct_monthly_revenue') }}
),

costs as (
    select
        cost_month                                      as month,
        infra_cost,
        marketing_cost,
        support_cost,
        total_cost
    from {{ ref('stg_costs') }}
),

joined as (
    select
        coalesce(r.month, c.month)                      as month,
        coalesce(r.revenue, 0)                          as revenue,
        coalesce(c.infra_cost, 0)                       as infra_cost,
        coalesce(c.marketing_cost, 0)                   as marketing_cost,
        coalesce(c.support_cost, 0)                     as support_cost,
        coalesce(c.total_cost, 0)                       as total_cost,
        coalesce(r.revenue, 0) - coalesce(c.total_cost, 0)
                                                        as gross_profit,
        round(
            (coalesce(r.revenue, 0) - coalesce(c.total_cost, 0))
            / nullif(coalesce(r.revenue, 0), 0) * 100,
            2
        )                                               as gross_margin_pct
    from revenue r
    full outer join costs c on r.month = c.month
)

select
    month,
    revenue,
    infra_cost,
    marketing_cost,
    support_cost,
    total_cost,
    gross_profit,
    gross_margin_pct,
    lag(gross_margin_pct) over (order by month)         as prev_month_gross_margin_pct
from joined
order by month desc
