{{
    config(
        materialized='view'
    )
}}

/*
    Staging model for CBB venues.
    
    Grain: 1 row per venue
*/

with source as (
    select * from {{ source('cbb', 'venues') }}
)

select
    id as venue_id,
    source_id,
    name as venue_name,
    city,
    state,
    country,
    load_date
from source
