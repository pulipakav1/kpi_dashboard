with customers as (
    select * from {{ ref('stg_customers') }}
),

subscriptions as (
    select * from {{ ref('stg_subscriptions') }}
),

payments as (
    select * from {{ ref('stg_payments') }}
),

customer_revenue as (
    select
        customer_id,
        sum(amount)                                     as total_revenue,
        count(*)                                        as total_payments,
        min(payment_date)                               as first_payment_date,
        max(payment_date)                               as last_payment_date
    from payments
    where is_successful = true
    group by customer_id
),

customer_subscription as (
    select distinct on (customer_id)
        customer_id,
        plan_type                                       as current_plan,
        monthly_price                                   as current_monthly_price,
        start_date                                      as subscription_start_date,
        is_active                                       as has_active_subscription
    from subscriptions
    order by customer_id, start_date desc
),

final as (
    select
        c.customer_id,
        c.signup_date,
        c.segment,
        c.country,
        c.acquisition_channel,
        c.is_active,
        c.customer_tenure_years,
        cs.current_plan,
        cs.current_monthly_price,
        cs.has_active_subscription,
        coalesce(cr.total_revenue, 0)                   as lifetime_value,
        coalesce(cr.total_payments, 0)                  as total_payments,
        cr.first_payment_date,
        cr.last_payment_date,
        case
            when coalesce(cr.total_revenue, 0) > 1000   then 'high'
            when coalesce(cr.total_revenue, 0) > 500    then 'medium'
            else 'low'
        end                                             as ltv_tier
    from customers c
    left join customer_subscription cs using (customer_id)
    left join customer_revenue cr using (customer_id)
)

select * from final
