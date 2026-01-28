{{
    config(
        materialized='view'
    )
}}

/*
    Staging model for per-game team stats.
    
    Grain: 1 row per game per team (ts_* for team, os_* for opponent).
    This keeps the ingested snake_case columns as-is and adds a parsed game_date.
*/

select
    game_id,
    season,
    season_label,
    season_type,
    start_date::date as game_date,
    tournament,
    game_type,
    neutral_site,
    is_home,
    conference_game,
    team_id,
    team,
    conference,
    team_seed,
    opponent_id,
    opponent,
    opponent_conference,
    opponent_seed,
    -- keep all remaining stat columns
    {{ dbt_utils.star(from=source('cbb', 'game_team_stats'), except=[
        'game_id','season','season_label','season_type','start_date','tournament','game_type',
        'neutral_site','is_home','conference_game','team_id','team','conference','team_seed',
        'opponent_id','opponent','opponent_conference','opponent_seed'
    ]) }}
from {{ source('cbb', 'game_team_stats') }}
