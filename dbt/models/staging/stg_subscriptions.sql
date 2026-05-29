with source as (
    select * from {{ source('raw', 'subscriptions') }}
),

renamed as (
    select
        subscription_id,
        customer_id,
        lower(trim(plan_type))                          as plan_type,
        cast(start_date as date)                        as start_date,
        cast(end_date as date)                          as end_date,
        cast(monthly_price as numeric(10, 2))           as monthly_price,
        case when end_date is null then true else false end
                                                        as is_active,
        case
            when end_date is not null
            then end_date - start_date
        end                                             as subscription_duration_days
    from source
    where subscription_id is not null
      and customer_id is not null
      and cast(monthly_price as numeric) >= 0
)

select * from renamed
