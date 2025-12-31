{{
    config(
        materialized='view',
        tags=['staging', 'cbb']
    )
}}

/*
    Staging model for CBB betting lines.
    Deduplicates multiple providers per game - picks first available.
    Standardizes spread sign: negative = home favored.
    One row per game with closing lines and final scores.
*/

with source as (
    select * from {{ source('cbb_raw', 'betting_lines') }}
),

-- Deduplicate: pick one line per game (prefer non-null spread)
ranked as (
    select
        *,
        row_number() over (
            partition by game_id
            order by
                case when spread is not null then 0 else 1 end,
                case when over_under is not null then 0 else 1 end,
                id  -- tiebreaker
        ) as rn
    from source
    where game_id is not null
),

deduplicated as (
    select * from ranked where rn = 1
),

cleaned as (
    select
        -- Keys
        game_id,

        -- Season context
        season,
        season_type,
        start_date as game_date,

        -- Teams (denormalized)
        home_team_id,
        upper(trim(home_team)) as home_team,
        home_conference,
        away_team_id,
        upper(trim(away_team)) as away_team,
        away_conference,

        -- Closing lines
        -- Spread convention: negative = home favored (already correct)
        spread as closing_spread_home,
        spread_open as opening_spread_home,
        over_under as closing_total,
        over_under_open as opening_total,

        -- Moneylines
        home_moneyline,
        away_moneyline,

        -- Final scores
        home_score::numeric as home_score,
        away_score::numeric as away_score,

        -- Line provider (for reference)
        provider,

        -- Derived: line movement
        case
            when spread is not null and spread_open is not null
            then spread - spread_open
            else null
        end as spread_movement,

        case
            when over_under is not null and over_under_open is not null
            then over_under - over_under_open
            else null
        end as total_movement,

        -- Metadata
        created_at

    from deduplicated
    where
        -- Must have at least spread or total
        (spread is not null or over_under is not null)
)

select * from cleaned
