with source as (
    select * from {{ source('raw', 'payments') }}
),

renamed as (
    select
        payment_id,
        customer_id,
        cast(payment_date as date)                      as payment_date,
        date_trunc('month', cast(payment_date as date)) as payment_month,
        cast(amount as numeric(10, 2))                  as amount,
        lower(trim(payment_status))                     as payment_status,
        case when lower(trim(payment_status)) = 'success' then true else false end
                                                        as is_successful
    from source
    where payment_id is not null
      and cast(amount as numeric) > 0
)

select * from renamed
