{{
    config(
        materialized='view'
    )
}}

/*
    ============================================================================
    INTERMEDIATE MODEL: int_cbb__game_betting_outcomes
    ============================================================================

    PURPOSE:
    Consolidates Bovada betting lines with actual game outcomes to create
    the labels needed for ML training (O/U hit/miss, margin vs line).

    GRAIN: 1 row per game
    - Only games with Bovada O/U lines
    - Only completed games with final scores

    SOURCE TABLES:
    - cbb.games (game outcomes)
    - cbb.betting_lines (sportsbook lines)

    RAW COLUMN NAMES:
    - betting_lines.over_under (not total_close)
    - betting_lines.over_under_open
    - games.home_team_id, away_team_id
    - games.home_points, away_points

    ============================================================================
*/

with games as (
    select
        id as game_id,
        start_date::timestamp as game_timestamp,
        start_date::date as game_date,
        season,
        season_type,
        neutral_site as is_neutral_site,
        conference_game as is_conference_game,
        tournament,

        -- Home team
        home_team_id as home_id,
        home_team,
        home_conference,
        home_points,

        -- Away team
        away_team_id as away_id,
        away_team,
        away_conference,
        away_points,

        -- Pre-computed totals
        coalesce(home_points, 0) + coalesce(away_points, 0) as total_points,
        coalesce(home_points, 0) - coalesce(away_points, 0) as home_point_differential

    from {{ source('cbb', 'games') }}
    where home_points is not null
      and away_points is not null
),

bovada_lines as (
    select
        game_id,
        over_under_open as vegas_total_open,
        over_under as vegas_total,
        over_under - coalesce(over_under_open, over_under) as vegas_line_movement,
        spread as vegas_spread,
        spread - coalesce(spread_open, spread) as vegas_spread_movement

    from {{ source('cbb', 'betting_lines') }}
    where provider = 'Bovada'
      and over_under is not null
),

combined as (
    select
        -- =======================================================================
        -- GAME IDENTIFIERS
        -- =======================================================================
        g.game_id,
        g.game_date,
        g.game_timestamp,
        g.season,
        g.season_type,

        -- =======================================================================
        -- GAME CONTEXT
        -- =======================================================================
        g.is_neutral_site,
        g.is_conference_game,
        g.tournament,

        -- =======================================================================
        -- TEAMS
        -- =======================================================================
        g.home_id,
        g.home_team,
        g.home_conference,
        g.away_id,
        g.away_team,
        g.away_conference,

        -- =======================================================================
        -- ACTUAL SCORING
        -- =======================================================================
        g.home_points,
        g.away_points,
        g.total_points as actual_total,
        g.home_point_differential,

        -- =======================================================================
        -- VEGAS LINES (Bovada)
        -- =======================================================================
        b.vegas_total_open,
        b.vegas_total,
        b.vegas_line_movement,
        b.vegas_spread,
        b.vegas_spread_movement,

        -- =======================================================================
        -- O/U OUTCOME METRICS
        -- =======================================================================
        -- Margin: positive = over, negative = under
        g.total_points - b.vegas_total as total_margin,

        -- Absolute margin (for analyzing variance)
        abs(g.total_points - b.vegas_total) as total_margin_abs,

        -- O/U Result as category
        case
            when g.total_points > b.vegas_total then 'OVER'
            when g.total_points < b.vegas_total then 'UNDER'
            else 'PUSH'
        end as ou_result,

        -- Binary label for ML classification (1 = over hit, 0 = under/push)
        case
            when g.total_points > b.vegas_total then 1
            else 0
        end as over_hit,

        -- Indicator flags
        case when g.total_points = b.vegas_total then 1 else 0 end as is_push

    from games g
    inner join bovada_lines b on g.game_id = b.game_id
)

select * from combined
