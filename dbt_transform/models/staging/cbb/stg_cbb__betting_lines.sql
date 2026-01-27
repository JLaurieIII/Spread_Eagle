{{
    config(
        materialized='view'
    )
}}

/*
    Staging model for CBB betting lines.
    
    Grain: 1 row per game per provider
    Source: cbb.betting_lines (flattened ingest)
    
    Transformations:
    - Standardize column names
    - Calculate line movement (close - open)
    - Filter to rows with a posted total (needed for OU analysis)
*/

with source as (
    select * from {{ source('cbb', 'betting_lines') }}
),

cleaned as (
    select
        -- Keys
        game_id,
        provider,
        
        -- Game context
        season,
        season_type,
        start_date::date as game_date,
        
        -- Teams/scores
        home_team_id,
        home_team,
        home_conference,
        home_score,
        away_team_id,
        away_team,
        away_conference,
        away_score,
        
        -- Spread (home perspective)
        spread_open,
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
    where over_under is not null
)

select * from cleaned
