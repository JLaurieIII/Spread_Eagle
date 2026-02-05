{{
    config(
        materialized='table'
    )
}}

/*
    ============================================================================
    INTERMEDIATE MODEL: int_cbb__team_ou_trends
    ============================================================================

    PURPOSE:
    Calculate rolling Over/Under trends for each team. Tracks how often
    a team's games go over or under the total, helping identify teams
    that consistently play in high/low-scoring games.

    KEY INSIGHT:
    Some teams consistently play in games that go over (fast pace, poor defense)
    while others consistently go under (slow pace, good defense). This helps
    predict O/U outcomes based on team tendencies.

    GRAIN: 1 row per game per team
    - Rolling windows: L5, L10 (last 5, 10 games)
    - All metrics EXCLUDE current game (no data leakage)
    - Partitioned by team + season

    METRICS:
    - Over rate = % of games that went over
    - Under rate = % of games that went under
    - Total margin = actual total - line (positive = over, negative = under)
    - Avg total in team's games

    ============================================================================
*/

with game_ou_results as (
    -- Get O/U outcomes for each team's games
    select
        bo.game_id,
        bo.game_date,
        bo.season,
        -- Team perspective (home)
        bo.home_id as team_id,
        bo.home_team as team_name,
        bo.actual_total,
        bo.vegas_total,
        bo.total_margin,
        bo.ou_result,
        bo.over_hit,
        case when bo.ou_result = 'UNDER' then 1 else 0 end as under_hit,
        case when bo.ou_result = 'PUSH' then 1 else 0 end as push_hit,
        true as is_home
    from {{ ref('int_cbb__game_betting_outcomes') }} bo
    where bo.vegas_total is not null

    union all

    select
        bo.game_id,
        bo.game_date,
        bo.season,
        -- Team perspective (away)
        bo.away_id as team_id,
        bo.away_team as team_name,
        bo.actual_total,
        bo.vegas_total,
        bo.total_margin,
        bo.ou_result,
        bo.over_hit,
        case when bo.ou_result = 'UNDER' then 1 else 0 end as under_hit,
        case when bo.ou_result = 'PUSH' then 1 else 0 end as push_hit,
        false as is_home
    from {{ ref('int_cbb__game_betting_outcomes') }} bo
    where bo.vegas_total is not null
),

ordered_games as (
    select
        *,
        -- Tightness to total line (exclusive: < not <= because exactly at boundary = loss)
        case when abs(total_margin) < 5 then 1 else 0 end as within_5_of_total,
        case when abs(total_margin) < 6 then 1 else 0 end as within_6_of_total,
        case when abs(total_margin) < 7 then 1 else 0 end as within_7_of_total,
        case when abs(total_margin) < 8 then 1 else 0 end as within_8_of_total,
        case when abs(total_margin) < 10 then 1 else 0 end as within_10_of_total,
        -- Game number within season
        row_number() over (
            partition by team_id, season
            order by game_date, game_id
        ) as season_game_num
    from game_ou_results
),

rolling_ou_trends as (
    select
        game_id,
        game_date,
        season,
        team_id,
        team_name,
        is_home,
        actual_total,
        vegas_total,
        total_margin,
        ou_result,
        -- Raw within_X_of_total flags for this game (for testing/debugging)
        within_5_of_total,
        within_6_of_total,
        within_7_of_total,
        within_8_of_total,
        within_10_of_total,
        season_game_num,

        -- Games played (excluding current)
        season_game_num - 1 as games_played,

        -- =======================================================================
        -- OVER/UNDER RATES (higher over_rate = games tend to go over)
        -- =======================================================================
        avg(over_hit::float) over w_prev_5 as over_rate_l5,
        avg(over_hit::float) over w_prev_10 as over_rate_l10,
        avg(under_hit::float) over w_prev_5 as under_rate_l5,
        avg(under_hit::float) over w_prev_10 as under_rate_l10,

        -- =======================================================================
        -- TOTAL MARGIN STATS (positive = team's games tend to go over)
        -- =======================================================================
        avg(total_margin) over w_prev_5 as avg_total_margin_l5,
        avg(total_margin) over w_prev_10 as avg_total_margin_l10,
        stddev_samp(total_margin) over w_prev_5 as stddev_total_margin_l5,
        stddev_samp(total_margin) over w_prev_10 as stddev_total_margin_l10,

        -- =======================================================================
        -- AVERAGE GAME TOTALS (helps gauge team's scoring environment)
        -- =======================================================================
        avg(actual_total) over w_prev_5 as avg_actual_total_l5,
        avg(actual_total) over w_prev_10 as avg_actual_total_l10,
        avg(vegas_total) over w_prev_5 as avg_vegas_total_l5,
        avg(vegas_total) over w_prev_10 as avg_vegas_total_l10,

        -- =======================================================================
        -- EXTREMES (for identifying high/low scoring tendencies)
        -- =======================================================================
        max(total_margin) over w_prev_10 as max_over_margin_l10,
        min(total_margin) over w_prev_10 as max_under_margin_l10,

        -- =======================================================================
        -- STREAK INDICATORS
        -- =======================================================================
        sum(over_hit) over w_prev_3 as overs_last_3,
        sum(under_hit) over w_prev_3 as unders_last_3,

        -- =======================================================================
        -- TIGHTNESS TO TOTAL (higher = more predictable totals)
        -- =======================================================================
        avg(within_5_of_total::float) over w_prev_10 as within_5_total_rate_l10,
        avg(within_6_of_total::float) over w_prev_10 as within_6_total_rate_l10,
        avg(within_7_of_total::float) over w_prev_10 as within_7_total_rate_l10,
        avg(within_8_of_total::float) over w_prev_10 as within_8_total_rate_l10,
        avg(within_10_of_total::float) over w_prev_10 as within_10_total_rate_l10

    from ordered_games

    window
        w_prev_3 as (
            partition by team_id, season
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ),
        w_prev_5 as (
            partition by team_id, season
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ),
        w_prev_10 as (
            partition by team_id, season
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        )
)

select * from rolling_ou_trends
order by game_date desc, game_id, team_id
