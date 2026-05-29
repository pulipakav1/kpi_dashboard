with source as (
    select * from {{ source('raw', 'costs') }}
),

renamed as (
    select
        to_date(month || '-01', 'YYYY-MM-DD')           as cost_month,
        month                                           as month_key,
        cast(infra_cost as numeric(10, 2))              as infra_cost,
        cast(marketing_cost as numeric(10, 2))          as marketing_cost,
        cast(support_cost as numeric(10, 2))            as support_cost,
        cast(infra_cost as numeric)
            + cast(marketing_cost as numeric)
            + cast(support_cost as numeric)             as total_cost
    from source
    where month is not null
)

select * from renamed
