{{
    config(
        materialized='view',
        tags=['intermediate', 'cbb', 'shape']
    )
}}

/*
    TREND STATE VIEW (vw_team_trend_state)

    Purpose: Short-term ATS/total trends + variance contraction/expansion.
    Key insight: Variance contracting = team stabilizing = higher confidence.

    Metrics by rolling window (3, 5, 10, 20 games):
    - ATS/O-U win rates (trend direction)
    - Current streak (hot/cold detection)
    - Variance contraction signals (comparing short vs long windows)
*/

with team_games as (
    select * from {{ ref('int_cbb_team_game') }}
),

spread_behavior as (
    select * from {{ ref('int_cbb_team_spread_behavior') }}
),

total_behavior as (
    select * from {{ ref('int_cbb_team_total_behavior') }}
),

-- Calculate streaks using lag
streak_calc as (
    select
        tg.game_id,
        tg.team_id,
        tg.team,
        tg.game_date,
        tg.season,
        tg.team_game_number,
        tg.ats_win_team,
        tg.over_win,

        -- Lag values for streak detection
        lag(tg.ats_win_team, 1) over (
            partition by tg.team_id order by tg.game_date, tg.game_id
        ) as ats_win_lag1,
        lag(tg.ats_win_team, 2) over (
            partition by tg.team_id order by tg.game_date, tg.game_id
        ) as ats_win_lag2,
        lag(tg.ats_win_team, 3) over (
            partition by tg.team_id order by tg.game_date, tg.game_id
        ) as ats_win_lag3,
        lag(tg.ats_win_team, 4) over (
            partition by tg.team_id order by tg.game_date, tg.game_id
        ) as ats_win_lag4,

        lag(tg.over_win, 1) over (
            partition by tg.team_id order by tg.game_date, tg.game_id
        ) as over_win_lag1,
        lag(tg.over_win, 2) over (
            partition by tg.team_id order by tg.game_date, tg.game_id
        ) as over_win_lag2,
        lag(tg.over_win, 3) over (
            partition by tg.team_id order by tg.game_date, tg.game_id
        ) as over_win_lag3,
        lag(tg.over_win, 4) over (
            partition by tg.team_id order by tg.game_date, tg.game_id
        ) as over_win_lag4

    from team_games tg
),

-- Calculate rolling ATS/OU rates
rolling_rates as (
    select
        game_id,
        team_id,
        team,
        game_date,
        season,
        team_game_number,
        ats_win_team,
        over_win,
        ats_win_lag1,
        ats_win_lag2,
        ats_win_lag3,
        ats_win_lag4,
        over_win_lag1,
        over_win_lag2,
        over_win_lag3,
        over_win_lag4,

        -- Rolling ATS win rates (excluding pushes via NULL)
        avg(ats_win_team::numeric) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as ats_win_rate_last3,

        avg(ats_win_team::numeric) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as ats_win_rate_last5,

        avg(ats_win_team::numeric) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as ats_win_rate_last10,

        avg(ats_win_team::numeric) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as ats_win_rate_last20,

        -- Rolling O/U rates
        avg(over_win::numeric) over (
            partition by team_id
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as over_rate_last3,

        avg(over_win::numeric) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as over_rate_last5,

        avg(over_win::numeric) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as over_rate_last10,

        avg(over_win::numeric) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as over_rate_last20

    from streak_calc
),

-- Calculate streaks (consecutive wins/losses ATS and O/U)
with_streaks as (
    select
        rr.*,

        -- ATS streak (positive = winning streak, negative = losing)
        case
            when ats_win_lag1 = 1 and ats_win_lag2 = 1 and ats_win_lag3 = 1 and ats_win_lag4 = 1 then 4
            when ats_win_lag1 = 1 and ats_win_lag2 = 1 and ats_win_lag3 = 1 then 3
            when ats_win_lag1 = 1 and ats_win_lag2 = 1 then 2
            when ats_win_lag1 = 1 then 1
            when ats_win_lag1 = 0 and ats_win_lag2 = 0 and ats_win_lag3 = 0 and ats_win_lag4 = 0 then -4
            when ats_win_lag1 = 0 and ats_win_lag2 = 0 and ats_win_lag3 = 0 then -3
            when ats_win_lag1 = 0 and ats_win_lag2 = 0 then -2
            when ats_win_lag1 = 0 then -1
            else 0
        end as ats_streak,

        -- Over streak (positive = over streak, negative = under)
        case
            when over_win_lag1 = 1 and over_win_lag2 = 1 and over_win_lag3 = 1 and over_win_lag4 = 1 then 4
            when over_win_lag1 = 1 and over_win_lag2 = 1 and over_win_lag3 = 1 then 3
            when over_win_lag1 = 1 and over_win_lag2 = 1 then 2
            when over_win_lag1 = 1 then 1
            when over_win_lag1 = 0 and over_win_lag2 = 0 and over_win_lag3 = 0 and over_win_lag4 = 0 then -4
            when over_win_lag1 = 0 and over_win_lag2 = 0 and over_win_lag3 = 0 then -3
            when over_win_lag1 = 0 and over_win_lag2 = 0 then -2
            when over_win_lag1 = 0 then -1
            else 0
        end as over_under_streak

    from rolling_rates rr
),

-- Join with behavior views for variance metrics
final as (
    select
        ws.game_id,
        ws.team_id,
        ws.team,
        ws.game_date,
        ws.season,
        ws.team_game_number,

        -- Current game results (for validation, not features)
        ws.ats_win_team,
        ws.over_win,

        -- ATS win rates
        ws.ats_win_rate_last3,
        ws.ats_win_rate_last5,
        ws.ats_win_rate_last10,
        ws.ats_win_rate_last20,

        -- O/U rates
        ws.over_rate_last3,
        ws.over_rate_last5,
        ws.over_rate_last10,
        ws.over_rate_last20,

        -- Streaks
        ws.ats_streak,
        ws.over_under_streak,

        -- Variance from spread behavior
        sb.stddev_cover_margin_last3,
        sb.stddev_cover_margin_last5,
        sb.stddev_cover_margin_last10,
        sb.stddev_cover_margin_last20,

        -- Variance from total behavior
        tb.stddev_total_error_last3,
        tb.stddev_total_error_last5,
        tb.stddev_total_error_last10,
        tb.stddev_total_error_last20,

        -- =====================================================
        -- VARIANCE CONTRACTION SIGNALS
        -- Comparing short window to long window
        -- Ratio < 1 = variance contracting = stabilizing
        -- =====================================================

        -- Spread variance contraction (3 vs 10)
        case
            when sb.stddev_cover_margin_last10 > 0
            then sb.stddev_cover_margin_last3 / sb.stddev_cover_margin_last10
            else null
        end as spread_variance_contraction_3v10,

        -- Spread variance contraction (5 vs 20)
        case
            when sb.stddev_cover_margin_last20 > 0
            then sb.stddev_cover_margin_last5 / sb.stddev_cover_margin_last20
            else null
        end as spread_variance_contraction_5v20,

        -- Total variance contraction (3 vs 10)
        case
            when tb.stddev_total_error_last10 > 0
            then tb.stddev_total_error_last3 / tb.stddev_total_error_last10
            else null
        end as total_variance_contraction_3v10,

        -- Total variance contraction (5 vs 20)
        case
            when tb.stddev_total_error_last20 > 0
            then tb.stddev_total_error_last5 / tb.stddev_total_error_last20
            else null
        end as total_variance_contraction_5v20,

        -- =====================================================
        -- TREND DIRECTION FLAGS
        -- Is short-term performance diverging from long-term?
        -- =====================================================

        -- ATS hot (short-term > long-term by 10%+)
        case
            when ws.ats_win_rate_last3 is not null
                 and ws.ats_win_rate_last10 is not null
                 and ws.ats_win_rate_last3 > ws.ats_win_rate_last10 + 0.10
            then true else false
        end as ats_hot_trend,

        -- ATS cold (short-term < long-term by 10%+)
        case
            when ws.ats_win_rate_last3 is not null
                 and ws.ats_win_rate_last10 is not null
                 and ws.ats_win_rate_last3 < ws.ats_win_rate_last10 - 0.10
            then true else false
        end as ats_cold_trend,

        -- Over trending (going over more recently)
        case
            when ws.over_rate_last3 is not null
                 and ws.over_rate_last10 is not null
                 and ws.over_rate_last3 > ws.over_rate_last10 + 0.10
            then true else false
        end as over_trend_hot,

        -- Under trending (going under more recently)
        case
            when ws.over_rate_last3 is not null
                 and ws.over_rate_last10 is not null
                 and ws.over_rate_last3 < ws.over_rate_last10 - 0.10
            then true else false
        end as under_trend_hot

    from with_streaks ws
    left join spread_behavior sb
        on ws.game_id = sb.game_id and ws.team_id = sb.team_id
    left join total_behavior tb
        on ws.game_id = tb.game_id and ws.team_id = tb.team_id
)

select * from final
