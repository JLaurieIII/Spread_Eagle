{{
    config(
        materialized='view'
    )
}}

/*
    Staging model for CBB games.
    
    Grain: 1 row per game
    Source: cbb.games (flattened ingest)
    
    Transformations:
    - Normalize column names
    - Parse start_date into date/timestamp
    - Keep neutral/conference flags for downstream splits
    - Compute total points
*/

with source as (
    select * from {{ source('cbb', 'games') }}
),

cleaned as (
    select
        -- Primary key
        id as game_id,
        
        -- Game metadata
        season,
        season_label,
        season_type,
        tournament,
        game_type,
        status,
        start_date::timestamp as game_timestamp,
        start_date::date as game_date,
        start_time_tbd as is_start_time_tbd,
        neutral_site as is_neutral_site,
        conference_game as is_conference_game,
        game_notes,
        
        -- Venue/context
        venue_id,
        venue,
        city,
        state,
        attendance,
        
        -- Home team
        home_team_id as home_id,
        home_team,
        home_conference_id,
        home_conference,
        home_seed,
        home_points,
        home_period_points,
        home_winner,
        
        -- Away team
        away_team_id as away_id,
        away_team,
        away_conference_id,
        away_conference,
        away_seed,
        away_points,
        away_period_points,
        away_winner,
        
        -- Computed totals
        coalesce(home_points, 0) + coalesce(away_points, 0) as total_points,
        coalesce(home_points, 0) - coalesce(away_points, 0) as home_point_differential,
        
        -- Metadata
        load_date
        
    from source
    where home_points is not null
      and away_points is not null
)

select * from cleaned
