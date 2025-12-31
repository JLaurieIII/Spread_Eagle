{{
    config(
        materialized='view',
        tags=['staging', 'cbb']
    )
}}

/*
    Staging model for CBB games.
    Cleans and standardizes raw game data.
    One row per completed game.
*/

with source as (
    select * from {{ source('cbb_raw', 'games') }}
),

cleaned as (
    select
        -- Primary key
        id as game_id,
        source_id,

        -- Season info
        season,
        season_label,
        season_type,
        tournament,

        -- Game timing
        start_date as game_date,
        date(start_date) as game_date_local,
        start_time_tbd,

        -- Game context
        neutral_site,
        conference_game,
        game_type,
        status,
        attendance,

        -- Home team
        home_team_id,
        upper(trim(home_team)) as home_team,
        home_conference_id,
        home_conference,
        home_seed,
        home_points as home_score,
        home_winner,

        -- Away team
        away_team_id,
        upper(trim(away_team)) as away_team,
        away_conference_id,
        away_conference,
        away_seed,
        away_points as away_score,
        away_winner,

        -- Venue
        venue_id,
        venue,
        city,
        state,

        -- Derived: game completion
        case
            when home_points is not null and away_points is not null
            then true
            else false
        end as is_completed,

        -- Metadata
        created_at

    from source
    where
        -- Only include games with valid data
        home_team_id is not null
        and away_team_id is not null
)

select * from cleaned
