{{
    config(
        materialized='view',
        tags=['intermediate', 'cbb', 'shape']
    )
}}

/*
    SPREAD BEHAVIOR VIEW (vw_team_spread_behavior)

    Quantifies how tightly a team plays around the spread.
    Key insight: Skinny distributions = predictable = teaser gold.

    CRITICAL: Uses ROWS BETWEEN N PRECEDING AND 1 PRECEDING
    to ensure NO LEAKAGE - only prior games inform features.

    Metrics by rolling window (3, 5, 10, 20 games):
    - Mean/StdDev of cover margin
    - Within-7 and within-10 rates (tight distributions)
    - Downside tail rate (teaser killers)
*/

with team_games as (
    select * from {{ ref('int_cbb_team_game') }}
),

rolling_stats as (
    select
        -- Keys
        game_id,
        team_id,
        team,
        game_date,
        season,
        team_game_number,
        is_home,

        -- Current game actuals (for reference, not features)
        cover_margin_team,
        ats_win_team,
        closing_spread_team,

        -- =====================================================
        -- ROLLING 3 GAME WINDOW
        -- =====================================================
        avg(cover_margin_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as mean_cover_margin_last3,

        stddev(cover_margin_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as stddev_cover_margin_last3,

        avg(abs(cover_margin_team)) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as mean_abs_cover_margin_last3,

        -- Within-7 rate (tight games)
        avg(case when abs(cover_margin_team) <= 7 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as within_7_rate_last3,

        -- Within-10 rate
        avg(case when abs(cover_margin_team) <= 10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as within_10_rate_last3,

        -- Downside tail (lost by 10+ vs spread - teaser killer)
        avg(case when cover_margin_team <= -10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as downside_tail_rate_last3,

        -- =====================================================
        -- ROLLING 5 GAME WINDOW
        -- =====================================================
        avg(cover_margin_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as mean_cover_margin_last5,

        stddev(cover_margin_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as stddev_cover_margin_last5,

        avg(abs(cover_margin_team)) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as mean_abs_cover_margin_last5,

        avg(case when abs(cover_margin_team) <= 7 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as within_7_rate_last5,

        avg(case when abs(cover_margin_team) <= 10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as within_10_rate_last5,

        avg(case when cover_margin_team <= -10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as downside_tail_rate_last5,

        -- =====================================================
        -- ROLLING 10 GAME WINDOW
        -- =====================================================
        avg(cover_margin_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as mean_cover_margin_last10,

        stddev(cover_margin_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as stddev_cover_margin_last10,

        avg(abs(cover_margin_team)) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as mean_abs_cover_margin_last10,

        avg(case when abs(cover_margin_team) <= 7 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as within_7_rate_last10,

        avg(case when abs(cover_margin_team) <= 10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as within_10_rate_last10,

        avg(case when cover_margin_team <= -10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as downside_tail_rate_last10,

        -- =====================================================
        -- ROLLING 20 GAME WINDOW
        -- =====================================================
        avg(cover_margin_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as mean_cover_margin_last20,

        stddev(cover_margin_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as stddev_cover_margin_last20,

        avg(abs(cover_margin_team)) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as mean_abs_cover_margin_last20,

        avg(case when abs(cover_margin_team) <= 7 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as within_7_rate_last20,

        avg(case when abs(cover_margin_team) <= 10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as within_10_rate_last20,

        avg(case when cover_margin_team <= -10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as downside_tail_rate_last20,

        -- Game count for minimum sample validation
        count(*) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as games_in_window_20

    from team_games
)

select * from rolling_stats
