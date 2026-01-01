{{
    config(
        materialized='view'
    )
}}

/*
    Staging model for CFB games.
    
    Grain: 1 row per game
    Source: cfb.games (raw from CFBD API)
    
    Transformations:
    - Parse start_date string to proper date/timestamp
    - Rename columns to snake_case conventions
    - Add computed fields (total_points, point_differential)
    - Filter to completed games only (for historical analysis)
*/

with source as (
    select * from {{ source('cfb', 'games') }}
),

cleaned as (
    select
        -- Primary key
        id as game_id,
        
        -- Game metadata
        season,
        week,
        season_type,
        
        -- Parse the date string to proper types
        start_date::timestamp as game_timestamp,
        start_date::date as game_date,
        
        -- Game context
        neutral_site as is_neutral_site,
        conference_game as is_conference_game,
        completed as is_completed,
        
        -- Venue
        venue_id,
        venue as venue_name,
        
        -- Home team
        home_id,
        home_team,
        home_conference,
        home_points,
        home_pregame_elo,
        home_postgame_elo,
        
        -- Away team
        away_id,
        away_team,
        away_conference,
        away_points,
        away_pregame_elo,
        away_postgame_elo,
        
        -- Computed fields
        coalesce(home_points, 0) + coalesce(away_points, 0) as total_points,
        coalesce(home_points, 0) - coalesce(away_points, 0) as home_point_differential,
        
        -- Metadata
        load_date
        
    from source
    -- Include ALL games (completed and upcoming)
)

select * from cleaned
