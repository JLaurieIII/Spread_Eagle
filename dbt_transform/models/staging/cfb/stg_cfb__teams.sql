{{
    config(
        materialized='view'
    )
}}

/*
    Staging model for CFB teams.
    
    Grain: 1 row per team
    Source: cfb.teams (raw from CFBD API)
    
    Transformations:
    - Standardize column names
    - Keep location data for travel distance calculations
*/

with source as (
    select * from {{ source('cfb', 'teams') }}
),

cleaned as (
    select
        -- Primary key
        id as team_id,
        
        -- Team identity
        school as team_name,
        mascot,
        abbreviation,
        
        -- Conference info
        conference,
        division,
        classification,  -- FBS, FCS, etc.
        
        -- Location (for travel distance calcs in rest_and_schedule_spots)
        city,
        state,
        latitude,
        longitude,
        
        -- Home venue
        venue_id,
        
        -- Metadata
        load_date
        
    from source
)

select * from cleaned
