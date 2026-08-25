with raw_source as (
    select
        row_id,
        order_id,
        customer_id,
        product_id,
        product_name, -- Bring this in to build the matching hash string
        order_date,
        ship_date,
        ship_mode,
        sales,
        quantity,
        discount,
        profit
    from {{ source('raw', 'superstore_transactions') }}
),

engineered_supply_chain_metrics as (
    select
        row_id,
        order_id,
        customer_id,
        -- Generate the EXACT matching cryptographic key to align with dim_products
        md5(concat(product_id, '||', product_name)) as product_surrogate_key,
        order_date,
        ship_date,
        ship_mode,
        sales,
        quantity,
        discount,
        profit,
        (ship_date - order_date) as shipping_lead_time_days,
        case 
            when profit < 0 then 1 
            else 0 
        end as is_margin_leak
    from raw_source
)

select * from engineered_supply_chain_metrics
