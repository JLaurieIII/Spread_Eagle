{{
    config(
        materialized='view'
    )
}}

/*
    Staging model for season-level team stats.
    
    Grain: 1 row per team per season.
*/

select
    season,
    season_label,
    team_id,
    team,
    conference,
    -- include remaining metrics
    {{ dbt_utils.star(from=source('cbb', 'team_season_stats'), except=[
        'season','season_label','team_id','team','conference'
    ]) }}
from {{ source('cbb', 'team_season_stats') }}
