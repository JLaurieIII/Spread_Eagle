{{
    config(
        materialized='view',
        tags=['intermediate', 'cbb', 'shape']
    )
}}

/*
    MARKET PROFILE VIEW (vw_market_profile)

    Purpose: What lines the team typically faces (and at what consistency).
    Key insight: A team consistently facing -6 to -8 spreads has different
    teaser value than one bouncing between +3 and -15.

    Metrics by rolling window (3, 5, 10, 20 games):
    - Mean/StdDev of spread faced
    - Mean/StdDev of total faced
    - Favorite/underdog rate
    - Line consistency (lower stddev = more predictable line environment)
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

        -- Current game lines
        closing_spread_team,
        closing_total,

        -- Whether team is favorite (negative spread) or underdog (positive spread)
        case when closing_spread_team < 0 then 1 else 0 end as is_favorite,
        case when closing_spread_team > 0 then 1 else 0 end as is_underdog,

        -- =====================================================
        -- ROLLING 3 GAME WINDOW - SPREAD PROFILE
        -- =====================================================
        avg(closing_spread_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as mean_spread_faced_last3,

        stddev(closing_spread_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as stddev_spread_faced_last3,

        avg(case when closing_spread_team < 0 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as favorite_rate_last3,

        -- =====================================================
        -- ROLLING 3 GAME WINDOW - TOTAL PROFILE
        -- =====================================================
        avg(closing_total) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as mean_total_faced_last3,

        stddev(closing_total) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as stddev_total_faced_last3,

        -- =====================================================
        -- ROLLING 5 GAME WINDOW - SPREAD PROFILE
        -- =====================================================
        avg(closing_spread_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as mean_spread_faced_last5,

        stddev(closing_spread_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as stddev_spread_faced_last5,

        avg(case when closing_spread_team < 0 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as favorite_rate_last5,

        -- =====================================================
        -- ROLLING 5 GAME WINDOW - TOTAL PROFILE
        -- =====================================================
        avg(closing_total) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as mean_total_faced_last5,

        stddev(closing_total) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as stddev_total_faced_last5,

        -- =====================================================
        -- ROLLING 10 GAME WINDOW - SPREAD PROFILE
        -- =====================================================
        avg(closing_spread_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as mean_spread_faced_last10,

        stddev(closing_spread_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as stddev_spread_faced_last10,

        avg(case when closing_spread_team < 0 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as favorite_rate_last10,

        -- =====================================================
        -- ROLLING 10 GAME WINDOW - TOTAL PROFILE
        -- =====================================================
        avg(closing_total) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as mean_total_faced_last10,

        stddev(closing_total) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as stddev_total_faced_last10,

        -- =====================================================
        -- ROLLING 20 GAME WINDOW - SPREAD PROFILE
        -- =====================================================
        avg(closing_spread_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as mean_spread_faced_last20,

        stddev(closing_spread_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as stddev_spread_faced_last20,

        avg(case when closing_spread_team < 0 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as favorite_rate_last20,

        -- =====================================================
        -- ROLLING 20 GAME WINDOW - TOTAL PROFILE
        -- =====================================================
        avg(closing_total) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as mean_total_faced_last20,

        stddev(closing_total) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as stddev_total_faced_last20,

        -- Game count for sample validation
        count(*) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as games_in_window_20

    from team_games
    where closing_spread_team is not null
      and closing_total is not null
),

-- Add derived consistency metrics
final as (
    select
        *,

        -- =====================================================
        -- LINE CONSISTENCY SCORES
        -- Lower stddev = Vegas has consistent view of team
        -- =====================================================

        -- Spread consistency (inverted stddev, higher = more consistent)
        case
            when stddev_spread_faced_last10 > 0
            then 1.0 / (1.0 + stddev_spread_faced_last10)
            else null
        end as spread_consistency_last10,

        case
            when stddev_spread_faced_last20 > 0
            then 1.0 / (1.0 + stddev_spread_faced_last20)
            else null
        end as spread_consistency_last20,

        -- Total consistency
        case
            when stddev_total_faced_last10 > 0
            then 1.0 / (1.0 + stddev_total_faced_last10)
            else null
        end as total_consistency_last10,

        case
            when stddev_total_faced_last20 > 0
            then 1.0 / (1.0 + stddev_total_faced_last20)
            else null
        end as total_consistency_last20,

        -- =====================================================
        -- SPREAD BUCKET (categorical for analysis)
        -- =====================================================
        case
            when mean_spread_faced_last10 <= -10 then 'heavy_favorite'
            when mean_spread_faced_last10 <= -5 then 'moderate_favorite'
            when mean_spread_faced_last10 < 0 then 'slight_favorite'
            when mean_spread_faced_last10 < 5 then 'slight_underdog'
            when mean_spread_faced_last10 < 10 then 'moderate_underdog'
            else 'heavy_underdog'
        end as typical_spread_bucket_last10

    from rolling_stats
)

select * from final
