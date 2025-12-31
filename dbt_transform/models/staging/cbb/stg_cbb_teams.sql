{{
    config(
        materialized='view',
        tags=['staging', 'cbb']
    )
}}

/*
    Staging model for CBB teams.
    Reference dimension table.
*/

with source as (
    select * from {{ source('cbb_raw', 'teams') }}
),

cleaned as (
    select
        id as team_id,
        source_id,
        upper(trim(school)) as team_name,
        mascot,
        abbreviation,
        display_name,
        short_display_name,
        conference_id,
        conference,
        current_venue_id,
        current_venue,
        current_city,
        current_state,
        created_at
    from source
)

select * from cleaned
