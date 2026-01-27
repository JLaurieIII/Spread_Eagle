{{
    config(
        materialized='view'
    )
}}

/*
    Staging model for CBB teams.
    
    Grain: 1 row per team
    Source: cbb.teams
    
    Transformations:
    - Normalize identifiers and naming
    - Preserve conference and location metadata
*/

with source as (
    select * from {{ source('cbb', 'teams') }}
),

cleaned as (
    select
        id as team_id,
        coalesce(display_name, short_display_name, school, abbreviation, id::text) as team_name,
        coalesce(short_display_name, display_name, school, abbreviation, id::text) as team_name_short,
        school,
        mascot,
        abbreviation as team_abbr,
        conference,
        conference_id,
        primary_color,
        secondary_color,
        current_venue_id,
        current_venue as venue_name,
        current_city as city,
        current_state as state,
        load_date
    from source
)

select * from cleaned
