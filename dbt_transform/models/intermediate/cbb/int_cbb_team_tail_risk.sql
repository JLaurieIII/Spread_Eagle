{{
    config(
        materialized='view',
        tags=['intermediate', 'cbb', 'shape']
    )
}}

/*
    TAIL RISK PROFILE VIEW (vw_tail_risk_profile)

    Purpose: Explicit blowout frequency for teaser blow-through risk.
    Key insight: Teasers fail when teams get blown out beyond the teaser cushion.
    A team with high downside_tail_15 rate will blow through +8 teasers.

    Metrics by rolling window (3, 5, 10, 20 games):
    - Downside tail rates at various thresholds (-10, -12, -15, -20)
    - Upside tail rates (for opponent perspective)
    - Blowout frequency (either direction)
    - Teaser survival estimates
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

        -- Current game actuals
        cover_margin_team,
        ats_win_team,

        -- =====================================================
        -- ROLLING 5 GAME WINDOW - TAIL RATES
        -- =====================================================

        -- Downside tails (failed to cover by X or more - teaser killers)
        avg(case when cover_margin_team <= -8 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as downside_tail_8_rate_last5,

        avg(case when cover_margin_team <= -10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as downside_tail_10_rate_last5,

        avg(case when cover_margin_team <= -12 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as downside_tail_12_rate_last5,

        avg(case when cover_margin_team <= -15 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as downside_tail_15_rate_last5,

        avg(case when cover_margin_team <= -20 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as downside_tail_20_rate_last5,

        -- Upside tails (covered by X or more - opponent's teaser killers)
        avg(case when cover_margin_team >= 10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as upside_tail_10_rate_last5,

        avg(case when cover_margin_team >= 15 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as upside_tail_15_rate_last5,

        -- Blowout rate (either direction)
        avg(case when abs(cover_margin_team) >= 15 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as blowout_rate_last5,

        -- =====================================================
        -- ROLLING 10 GAME WINDOW - TAIL RATES
        -- =====================================================

        avg(case when cover_margin_team <= -8 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as downside_tail_8_rate_last10,

        avg(case when cover_margin_team <= -10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as downside_tail_10_rate_last10,

        avg(case when cover_margin_team <= -12 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as downside_tail_12_rate_last10,

        avg(case when cover_margin_team <= -15 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as downside_tail_15_rate_last10,

        avg(case when cover_margin_team <= -20 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as downside_tail_20_rate_last10,

        avg(case when cover_margin_team >= 10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as upside_tail_10_rate_last10,

        avg(case when cover_margin_team >= 15 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as upside_tail_15_rate_last10,

        avg(case when abs(cover_margin_team) >= 15 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as blowout_rate_last10,

        -- =====================================================
        -- ROLLING 20 GAME WINDOW - TAIL RATES (STABLE)
        -- =====================================================

        avg(case when cover_margin_team <= -8 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as downside_tail_8_rate_last20,

        avg(case when cover_margin_team <= -10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as downside_tail_10_rate_last20,

        avg(case when cover_margin_team <= -12 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as downside_tail_12_rate_last20,

        avg(case when cover_margin_team <= -15 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as downside_tail_15_rate_last20,

        avg(case when cover_margin_team <= -20 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as downside_tail_20_rate_last20,

        avg(case when cover_margin_team >= 10 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as upside_tail_10_rate_last20,

        avg(case when cover_margin_team >= 15 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as upside_tail_15_rate_last20,

        avg(case when abs(cover_margin_team) >= 15 then 1.0 else 0.0 end) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as blowout_rate_last20,

        -- Worst case (min cover margin in window)
        min(cover_margin_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as worst_cover_margin_last10,

        min(cover_margin_team) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as worst_cover_margin_last20,

        -- Game count for validation
        count(*) over (
            partition by team_id
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as games_in_window_20

    from team_games
),

-- Add derived teaser safety metrics
final as (
    select
        *,

        -- =====================================================
        -- TEASER SURVIVAL ESTIMATES
        -- Based on historical tail rates
        -- Higher = safer for teasers
        -- =====================================================

        -- +8 teaser survival (1 - downside_tail_8_rate)
        1.0 - coalesce(downside_tail_8_rate_last10, 0) as teaser_8_survival_last10,
        1.0 - coalesce(downside_tail_8_rate_last20, 0) as teaser_8_survival_last20,

        -- +10 teaser survival
        1.0 - coalesce(downside_tail_10_rate_last10, 0) as teaser_10_survival_last10,
        1.0 - coalesce(downside_tail_10_rate_last20, 0) as teaser_10_survival_last20,

        -- =====================================================
        -- RISK TIER CLASSIFICATION
        -- Based on downside tail behavior
        -- =====================================================

        case
            when downside_tail_10_rate_last20 <= 0.05 then 'very_low_risk'
            when downside_tail_10_rate_last20 <= 0.10 then 'low_risk'
            when downside_tail_10_rate_last20 <= 0.20 then 'moderate_risk'
            when downside_tail_10_rate_last20 <= 0.30 then 'high_risk'
            else 'very_high_risk'
        end as teaser_risk_tier,

        -- =====================================================
        -- TAIL ASYMMETRY
        -- Positive = more upside than downside (good for teasers)
        -- Negative = more downside risk (bad for teasers)
        -- =====================================================

        coalesce(upside_tail_10_rate_last10, 0) - coalesce(downside_tail_10_rate_last10, 0)
            as tail_asymmetry_10_last10,

        coalesce(upside_tail_15_rate_last20, 0) - coalesce(downside_tail_15_rate_last20, 0)
            as tail_asymmetry_15_last20

    from rolling_stats
)

select * from final
