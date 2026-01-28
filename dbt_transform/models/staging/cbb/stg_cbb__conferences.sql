{{
    config(
        materialized='view'
    )
}}

/*
    Staging model for CBB conferences.
    
    Grain: 1 row per conference
*/

with source as (
    select * from {{ source('cbb', 'conferences') }}
)

select
    id as conference_id,
    source_id,
    name as conference_name,
    abbreviation as conference_abbr,
    short_name as conference_short_name,
    load_date
from source
