-- models/staging/stg_crypto_market.sql
-- This model cleans and standardizes the raw crypto market data

with source as (
    select * from {{ source('raw_data', 'crypto_market') }}
),

renamed as (
    select
        -- identifiers
        id              as coin_id,
        symbol          as coin_symbol,
        name            as coin_name,

        -- prices
        current_price,
        high_24h,
        low_24h,
        ath,
        atl,

        -- market data
        market_cap,
        market_cap_rank,
        total_volume,
        circulating_supply,
        total_supply,
        max_supply,

        -- changes
        price_change_24h,
        price_change_percentage_24h,
        market_cap_change_24h,
        market_cap_change_percentage_24h,

        -- timestamps
        last_updated,
        extracted_at

    from source
)

select * from renamed