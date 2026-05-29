with source as (
    select * from {{ source('raw', 'customers') }}
),

renamed as (
    select
        customer_id,
        cast(signup_date as date)                       as signup_date,
        lower(trim(segment))                            as segment,
        upper(trim(country))                            as country,
        lower(trim(acquisition_channel))                as acquisition_channel,
        is_active,
        date_part('year', age(current_date, cast(signup_date as date)))::int
                                                        as customer_tenure_years
    from source
    where customer_id is not null
)

select * from renamed
