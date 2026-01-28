{{
    config(
        materialized='view'
    )
}}

/*
    Staging model for season-level player stats.
    
    Grain: 1 row per athlete per season per team.
*/

select
    season,
    season_label,
    athlete_id,
    athlete_source_id,
    team_id,
    team,
    -- include remaining metrics
    {{ dbt_utils.star(from=source('cbb', 'player_season_stats'), except=[
        'season','season_label','athlete_id','athlete_source_id',
        'team_id','team'
    ]) }}
from {{ source('cbb', 'player_season_stats') }}
