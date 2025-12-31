{{
    config(
        materialized='view',
        tags=['intermediate', 'cbb', 'shape']
    )
}}

/*
    TOTAL BEHAVIOR VIEW (vw_team_total_behavior)

    Quantifies stability around O/U totals.
    Key insight: Teams that consistently hit near totals = predictable tempo.

    Metrics by rolling window (3, 5, 10, 20 games):
    - Mean/StdDev of total error
    - Within-8 and within-10 total rates
    - Over/Under tendencies
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

        -- Current game actuals
        total_points,
        total_error,
        over_win,
        closing_total,

        -- =====================================================
        -- ROLLING 3 GAME WINDOW
        -- =====================================================
        avg(total_error) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as mean_total_error_last3,

        stddev(total_error) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as stddev_total_error_last3,

        avg(abs(total_error)) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as mean_abs_total_error_last3,

        -- Within-8 total rate
        avg(case when abs(total_error) <= 8 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as within_8_total_rate_last3,

        -- Within-10 total rate
        avg(case when abs(total_error) <= 10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as within_10_total_rate_last3,

        -- Over rate (excluding pushes)
        avg(over_win::numeric) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as over_rate_last3,

        -- =====================================================
        -- ROLLING 5 GAME WINDOW
        -- =====================================================
        avg(total_error) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as mean_total_error_last5,

        stddev(total_error) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as stddev_total_error_last5,

        avg(abs(total_error)) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as mean_abs_total_error_last5,

        avg(case when abs(total_error) <= 8 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as within_8_total_rate_last5,

        avg(case when abs(total_error) <= 10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as within_10_total_rate_last5,

        avg(over_win::numeric) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as over_rate_last5,

        -- =====================================================
        -- ROLLING 10 GAME WINDOW
        -- =====================================================
        avg(total_error) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as mean_total_error_last10,

        stddev(total_error) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as stddev_total_error_last10,

        avg(abs(total_error)) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as mean_abs_total_error_last10,

        avg(case when abs(total_error) <= 8 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as within_8_total_rate_last10,

        avg(case when abs(total_error) <= 10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as within_10_total_rate_last10,

        avg(over_win::numeric) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as over_rate_last10,

        -- =====================================================
        -- ROLLING 20 GAME WINDOW
        -- =====================================================
        avg(total_error) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as mean_total_error_last20,

        stddev(total_error) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as stddev_total_error_last20,

        avg(abs(total_error)) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as mean_abs_total_error_last20,

        avg(case when abs(total_error) <= 8 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as within_8_total_rate_last20,

        avg(case when abs(total_error) <= 10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as within_10_total_rate_last20,

        avg(over_win::numeric) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as over_rate_last20

    from team_games
)

select * from rolling_stats
