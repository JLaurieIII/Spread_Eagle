{{
    config(
        materialized='view'
    )
}}

/*
    Staging model for CFB betting lines.
    
    Grain: 1 row per game per provider
    Source: cfb.betting_lines (raw from CFBD API)
    
    Transformations:
    - Standardize column names
    - Calculate line movement (close - open)
    - Handle null spreads/totals
    
    Note: spread is from HOME team perspective
    (negative = home favored, positive = away favored)
*/

with source as (
    select * from {{ source('cfb', 'betting_lines') }}
),

cleaned as (
    select
        -- Keys
        game_id,
        provider,
        
        -- Game context
        season,
        season_type,
        week,
        start_date::date as game_date,
        
        -- Teams
        home_team_id,
        home_team,
        home_conference,
        away_team_id,
        away_team,
        away_conference,
        
        -- Scores (for calculating results)
        home_score,
        away_score,
        
        -- Spread (from home perspective)
        spread_open as spread_open,
        spread as spread_close,
        spread - coalesce(spread_open, spread) as spread_movement,
        
        -- Totals
        over_under_open as total_open,
        over_under as total_close,
        over_under - coalesce(over_under_open, over_under) as total_movement,
        
        -- Moneylines
        home_moneyline,
        away_moneyline,
        
        -- Metadata
        load_date
        
    from source
    where spread is not null  -- Must have a spread to be useful
)

select * from cleaned
