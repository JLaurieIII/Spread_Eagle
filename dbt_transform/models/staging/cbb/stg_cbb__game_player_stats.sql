{{
    config(
        materialized='view'
    )
}}

/*
    Staging model for per-game player stats.
    
    Grain: 1 row per game per athlete.
    Keeps all numeric/stat columns intact for downstream rollups.
*/

select
    game_id,
    season,
    season_label,
    season_type,
    start_date::date as game_date,
    team_id,
    opponent_id,
    athlete_id,
    athlete_source_id,
    is_home,
    -- include remaining stat columns
    {{ dbt_utils.star(from=source('cbb', 'game_player_stats'), except=[
        'game_id','season','season_label','season_type','start_date','team_id','opponent_id',
        'athlete_id','athlete_source_id','is_home'
    ]) }}
from {{ source('cbb', 'game_player_stats') }}
