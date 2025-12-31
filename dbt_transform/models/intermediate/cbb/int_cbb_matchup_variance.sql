{{
    config(
        materialized='view',
        tags=['intermediate', 'cbb', 'matchup']
    )
}}

/*
    MATCHUP VARIANCE INTERACTION VIEW (vw_matchup_variance_interaction)

    Purpose: Combine both teams' variance profiles into game-level predictions.
    Key insight: Two low-variance teams = premium teaser matchup.
    High variance vs high variance = chaos, avoid.

    Combines:
    - Both teams' spread behavior metrics
    - Both teams' tail risk profiles
    - Combined variance scores for the matchup
*/

with game_outcomes as (
    select * from {{ ref('int_cbb_game_outcomes') }}
),

spread_behavior as (
    select * from {{ ref('int_cbb_team_spread_behavior') }}
),

tail_risk as (
    select * from {{ ref('int_cbb_team_tail_risk') }}
),

trend_state as (
    select * from {{ ref('int_cbb_team_trend_state') }}
),

-- Get home team features
home_features as (
    select
        sb.game_id,
        sb.team_id as home_team_id,

        -- Spread behavior
        sb.stddev_cover_margin_last5 as home_stddev_cover_last5,
        sb.stddev_cover_margin_last10 as home_stddev_cover_last10,
        sb.stddev_cover_margin_last20 as home_stddev_cover_last20,
        sb.within_7_rate_last10 as home_within_7_rate_last10,
        sb.within_10_rate_last10 as home_within_10_rate_last10,
        sb.downside_tail_rate_last10 as home_downside_tail_10_rate_last10,
        sb.mean_cover_margin_last10 as home_mean_cover_last10,

        -- Tail risk
        tr.downside_tail_8_rate_last10 as home_tail_8_rate_last10,
        tr.downside_tail_10_rate_last10 as home_tail_10_rate_last10,
        tr.downside_tail_15_rate_last10 as home_tail_15_rate_last10,
        tr.teaser_8_survival_last10 as home_teaser_8_survival,
        tr.teaser_10_survival_last10 as home_teaser_10_survival,
        tr.teaser_risk_tier as home_teaser_risk_tier,
        tr.worst_cover_margin_last10 as home_worst_cover_last10,
        tr.blowout_rate_last10 as home_blowout_rate_last10,

        -- Trend state
        ts.ats_win_rate_last5 as home_ats_rate_last5,
        ts.ats_win_rate_last10 as home_ats_rate_last10,
        ts.ats_streak as home_ats_streak,
        ts.spread_variance_contraction_3v10 as home_variance_contraction,
        ts.ats_hot_trend as home_ats_hot,
        ts.ats_cold_trend as home_ats_cold

    from spread_behavior sb
    left join tail_risk tr
        on sb.game_id = tr.game_id and sb.team_id = tr.team_id
    left join trend_state ts
        on sb.game_id = ts.game_id and sb.team_id = ts.team_id
    where sb.is_home = true
),

-- Get away team features
away_features as (
    select
        sb.game_id,
        sb.team_id as away_team_id,

        -- Spread behavior
        sb.stddev_cover_margin_last5 as away_stddev_cover_last5,
        sb.stddev_cover_margin_last10 as away_stddev_cover_last10,
        sb.stddev_cover_margin_last20 as away_stddev_cover_last20,
        sb.within_7_rate_last10 as away_within_7_rate_last10,
        sb.within_10_rate_last10 as away_within_10_rate_last10,
        sb.downside_tail_rate_last10 as away_downside_tail_10_rate_last10,
        sb.mean_cover_margin_last10 as away_mean_cover_last10,

        -- Tail risk
        tr.downside_tail_8_rate_last10 as away_tail_8_rate_last10,
        tr.downside_tail_10_rate_last10 as away_tail_10_rate_last10,
        tr.downside_tail_15_rate_last10 as away_tail_15_rate_last10,
        tr.teaser_8_survival_last10 as away_teaser_8_survival,
        tr.teaser_10_survival_last10 as away_teaser_10_survival,
        tr.teaser_risk_tier as away_teaser_risk_tier,
        tr.worst_cover_margin_last10 as away_worst_cover_last10,
        tr.blowout_rate_last10 as away_blowout_rate_last10,

        -- Trend state
        ts.ats_win_rate_last5 as away_ats_rate_last5,
        ts.ats_win_rate_last10 as away_ats_rate_last10,
        ts.ats_streak as away_ats_streak,
        ts.spread_variance_contraction_3v10 as away_variance_contraction,
        ts.ats_hot_trend as away_ats_hot,
        ts.ats_cold_trend as away_ats_cold

    from spread_behavior sb
    left join tail_risk tr
        on sb.game_id = tr.game_id and sb.team_id = tr.team_id
    left join trend_state ts
        on sb.game_id = ts.game_id and sb.team_id = ts.team_id
    where sb.is_home = false
),

-- Combine into game-level matchup features
matchup as (
    select
        g.game_id,
        g.game_date,
        g.season,
        g.home_team_id,
        g.home_team,
        g.away_team_id,
        g.away_team,
        g.closing_spread_home,
        g.closing_total,
        g.cover_margin_home,
        g.total_error,
        g.ats_win_home,
        g.over_win,

        -- Home team features
        h.home_stddev_cover_last5,
        h.home_stddev_cover_last10,
        h.home_stddev_cover_last20,
        h.home_within_7_rate_last10,
        h.home_within_10_rate_last10,
        h.home_mean_cover_last10,
        h.home_tail_8_rate_last10,
        h.home_tail_10_rate_last10,
        h.home_tail_15_rate_last10,
        h.home_teaser_8_survival,
        h.home_teaser_10_survival,
        h.home_teaser_risk_tier,
        h.home_worst_cover_last10,
        h.home_blowout_rate_last10,
        h.home_ats_rate_last5,
        h.home_ats_rate_last10,
        h.home_ats_streak,
        h.home_variance_contraction,
        h.home_ats_hot,
        h.home_ats_cold,

        -- Away team features
        a.away_stddev_cover_last5,
        a.away_stddev_cover_last10,
        a.away_stddev_cover_last20,
        a.away_within_7_rate_last10,
        a.away_within_10_rate_last10,
        a.away_mean_cover_last10,
        a.away_tail_8_rate_last10,
        a.away_tail_10_rate_last10,
        a.away_tail_15_rate_last10,
        a.away_teaser_8_survival,
        a.away_teaser_10_survival,
        a.away_teaser_risk_tier,
        a.away_worst_cover_last10,
        a.away_blowout_rate_last10,
        a.away_ats_rate_last5,
        a.away_ats_rate_last10,
        a.away_ats_streak,
        a.away_variance_contraction,
        a.away_ats_hot,
        a.away_ats_cold,

        -- =====================================================
        -- COMBINED MATCHUP VARIANCE METRICS
        -- =====================================================

        -- Combined stddev (root sum of squares - variance adds)
        sqrt(
            power(coalesce(h.home_stddev_cover_last10, 10), 2) +
            power(coalesce(a.away_stddev_cover_last10, 10), 2)
        ) as combined_stddev_cover_last10,

        -- Average volatility (simple average of both teams)
        (coalesce(h.home_stddev_cover_last10, 10) + coalesce(a.away_stddev_cover_last10, 10)) / 2.0
            as avg_volatility_last10,

        -- Max volatility (most volatile team determines floor)
        greatest(
            coalesce(h.home_stddev_cover_last10, 10),
            coalesce(a.away_stddev_cover_last10, 10)
        ) as max_volatility_last10,

        -- Combined within-7 rate (both teams play tight)
        (coalesce(h.home_within_7_rate_last10, 0) + coalesce(a.away_within_7_rate_last10, 0)) / 2.0
            as combined_within_7_rate,

        -- Combined within-10 rate
        (coalesce(h.home_within_10_rate_last10, 0) + coalesce(a.away_within_10_rate_last10, 0)) / 2.0
            as combined_within_10_rate,

        -- =====================================================
        -- TEASER MATCHUP SAFETY SCORES
        -- =====================================================

        -- Combined teaser survival (product of both teams' survival)
        coalesce(h.home_teaser_8_survival, 0.8) * coalesce(a.away_teaser_8_survival, 0.8)
            as matchup_teaser_8_survival,

        coalesce(h.home_teaser_10_survival, 0.85) * coalesce(a.away_teaser_10_survival, 0.85)
            as matchup_teaser_10_survival,

        -- Worst blowout rate (either team can blow up the teaser)
        greatest(
            coalesce(h.home_blowout_rate_last10, 0),
            coalesce(a.away_blowout_rate_last10, 0)
        ) as matchup_blowout_risk,

        -- Combined tail risk (sum of downside tails)
        coalesce(h.home_tail_10_rate_last10, 0) + coalesce(a.away_tail_10_rate_last10, 0)
            as combined_tail_10_risk,

        -- =====================================================
        -- MATCHUP QUALITY TIERS
        -- =====================================================

        case
            when coalesce(h.home_stddev_cover_last10, 999) < 8
                 and coalesce(a.away_stddev_cover_last10, 999) < 8
                 and coalesce(h.home_blowout_rate_last10, 1) < 0.15
                 and coalesce(a.away_blowout_rate_last10, 1) < 0.15
            then 'premium'
            when coalesce(h.home_stddev_cover_last10, 999) < 10
                 and coalesce(a.away_stddev_cover_last10, 999) < 10
                 and coalesce(h.home_blowout_rate_last10, 1) < 0.25
                 and coalesce(a.away_blowout_rate_last10, 1) < 0.25
            then 'good'
            when coalesce(h.home_stddev_cover_last10, 999) < 12
                 and coalesce(a.away_stddev_cover_last10, 999) < 12
            then 'fair'
            else 'avoid'
        end as teaser_matchup_quality,

        -- Both teams contracting variance = stabilizing matchup
        case
            when coalesce(h.home_variance_contraction, 1) < 0.9
                 and coalesce(a.away_variance_contraction, 1) < 0.9
            then true else false
        end as both_teams_stabilizing,

        -- Trend clash (one hot, one cold)
        case
            when (h.home_ats_hot = true and a.away_ats_cold = true)
                 or (h.home_ats_cold = true and a.away_ats_hot = true)
            then true else false
        end as trend_clash

    from game_outcomes g
    left join home_features h on g.game_id = h.game_id
    left join away_features a on g.game_id = a.game_id
)

select * from matchup
