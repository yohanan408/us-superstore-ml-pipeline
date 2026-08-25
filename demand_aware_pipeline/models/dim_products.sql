{{ config(materialized='table') }}

with raw_source as (
    select
        product_id,
        category,
        sub_category,
        product_name,
        sales,
        quantity,
        profit
    from {{ source('raw', 'superstore_transactions') }}
),

aggregated_product_metrics as (
    select
        -- Create a unique cryptographic surrogate key combining the recycled ID and Name
        md5(concat(product_id, '||', product_name)) as product_surrogate_key,
        product_id as original_product_id,
        category,
        sub_category,
        product_name,
        sum(sales) as total_historical_sales,
        sum(quantity) as total_units_sold,
        sum(profit) as total_historical_profit,
        case 
            when sum(sales) > 0 then round((sum(profit) / sum(sales)) * 100, 2)
            else 0 
        end as avg_profit_margin_percentage
    from raw_source
    group by product_id, category, sub_category, product_name
)

select * from aggregated_product_metrics
