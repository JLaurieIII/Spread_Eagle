{{
    config(
        materialized='table',
        tags=['marts', 'cbb', 'ml']
    )
}}

/*
    FINAL ML-READY TEASER SPREAD DATASET

    This is the canonical dataset for training teaser prediction models.

    Structure:
    - One row per team-game (so 2 rows per game)
    - Features: All variance/behavior metrics from prior games (NO LEAKAGE)
    - Labels: Actual teaser outcomes (win_teased_6, win_teased_8, etc.)

    Key design decisions:
    - All features computed using ROWS BETWEEN N PRECEDING AND 1 PRECEDING
    - No current-game information in features
    - Labels computed from actual outcomes (for supervised learning)
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

trend_state as (
    select * from {{ ref('int_cbb_team_trend_state') }}
),

market_profile as (
    select * from {{ ref('int_cbb_team_market_profile') }}
),

tail_risk as (
    select * from {{ ref('int_cbb_team_tail_risk') }}
),

teaser_labels as (
    select * from {{ ref('int_cbb_teaser_labels') }}
)

select
    -- =====================================================
    -- IDENTIFIERS
    -- =====================================================
    tg.game_id,
    tg.team_id,
    tg.team,
    tg.opponent_id,
    tg.opponent,
    tg.game_date,
    tg.season,
    tg.team_game_number,
    tg.is_home,
    tg.conference_game,
    tg.neutral_site,

    -- =====================================================
    -- CURRENT GAME CONTEXT (KNOWN AT BET TIME)
    -- =====================================================
    tg.closing_spread_team,
    tg.closing_total,
    tg.opening_spread_team,
    tg.opening_total,
    tg.spread_movement,
    tg.total_movement,

    -- =====================================================
    -- SPREAD BEHAVIOR FEATURES (PRIOR GAMES ONLY)
    -- =====================================================
    sb.mean_cover_margin_last3,
    sb.stddev_cover_margin_last3,
    sb.mean_abs_cover_margin_last3,
    sb.within_7_rate_last3,
    sb.within_10_rate_last3,
    sb.downside_tail_rate_last3,

    sb.mean_cover_margin_last5,
    sb.stddev_cover_margin_last5,
    sb.mean_abs_cover_margin_last5,
    sb.within_7_rate_last5,
    sb.within_10_rate_last5,
    sb.downside_tail_rate_last5,

    sb.mean_cover_margin_last10,
    sb.stddev_cover_margin_last10,
    sb.mean_abs_cover_margin_last10,
    sb.within_7_rate_last10,
    sb.within_10_rate_last10,
    sb.downside_tail_rate_last10,

    sb.mean_cover_margin_last20,
    sb.stddev_cover_margin_last20,
    sb.mean_abs_cover_margin_last20,
    sb.within_7_rate_last20,
    sb.within_10_rate_last20,
    sb.downside_tail_rate_last20,

    sb.games_in_window_20 as spread_games_in_window,

    -- =====================================================
    -- TOTAL BEHAVIOR FEATURES (PRIOR GAMES ONLY)
    -- =====================================================
    tb.mean_total_error_last5,
    tb.stddev_total_error_last5,
    tb.mean_abs_total_error_last5,
    tb.within_8_total_rate_last5,
    tb.within_10_total_rate_last5,
    tb.over_rate_last5,

    tb.mean_total_error_last10,
    tb.stddev_total_error_last10,
    tb.mean_abs_total_error_last10,
    tb.within_8_total_rate_last10,
    tb.within_10_total_rate_last10,
    tb.over_rate_last10,

    tb.mean_total_error_last20,
    tb.stddev_total_error_last20,
    tb.mean_abs_total_error_last20,
    tb.within_8_total_rate_last20,
    tb.within_10_total_rate_last20,
    tb.over_rate_last20,

    -- =====================================================
    -- TREND STATE FEATURES
    -- =====================================================
    ts.ats_win_rate_last3,
    ts.ats_win_rate_last5,
    ts.ats_win_rate_last10,
    ts.ats_win_rate_last20,

    ts.ats_streak,
    ts.over_under_streak,

    ts.spread_variance_contraction_3v10,
    ts.spread_variance_contraction_5v20,
    ts.total_variance_contraction_3v10,
    ts.total_variance_contraction_5v20,

    ts.ats_hot_trend,
    ts.ats_cold_trend,
    ts.over_trend_hot,
    ts.under_trend_hot,

    -- =====================================================
    -- MARKET PROFILE FEATURES
    -- =====================================================
    mp.mean_spread_faced_last10,
    mp.stddev_spread_faced_last10,
    mp.favorite_rate_last10,
    mp.mean_total_faced_last10,
    mp.stddev_total_faced_last10,

    mp.mean_spread_faced_last20,
    mp.stddev_spread_faced_last20,
    mp.favorite_rate_last20,
    mp.mean_total_faced_last20,
    mp.stddev_total_faced_last20,

    mp.spread_consistency_last10,
    mp.spread_consistency_last20,
    mp.total_consistency_last10,
    mp.total_consistency_last20,
    mp.typical_spread_bucket_last10,

    -- =====================================================
    -- TAIL RISK FEATURES
    -- =====================================================
    tr.downside_tail_8_rate_last5,
    tr.downside_tail_10_rate_last5,
    tr.downside_tail_12_rate_last5,
    tr.downside_tail_15_rate_last5,
    tr.upside_tail_10_rate_last5,
    tr.blowout_rate_last5,

    tr.downside_tail_8_rate_last10,
    tr.downside_tail_10_rate_last10,
    tr.downside_tail_12_rate_last10,
    tr.downside_tail_15_rate_last10,
    tr.downside_tail_20_rate_last10,
    tr.upside_tail_10_rate_last10,
    tr.blowout_rate_last10,

    tr.downside_tail_8_rate_last20,
    tr.downside_tail_10_rate_last20,
    tr.downside_tail_15_rate_last20,
    tr.downside_tail_20_rate_last20,
    tr.upside_tail_10_rate_last20,
    tr.blowout_rate_last20,

    tr.worst_cover_margin_last10,
    tr.worst_cover_margin_last20,

    tr.teaser_8_survival_last10,
    tr.teaser_8_survival_last20,
    tr.teaser_10_survival_last10,
    tr.teaser_10_survival_last20,
    tr.teaser_risk_tier,
    tr.tail_asymmetry_10_last10,
    tr.tail_asymmetry_15_last20,

    -- =====================================================
    -- TARGET LABELS (ACTUAL OUTCOMES)
    -- =====================================================
    tl.ats_win_team,
    tl.ats_push_flag,
    tl.cover_margin_team,

    -- Teaser win labels
    tl.win_teased_6,
    tl.win_teased_7,
    tl.win_teased_8,
    tl.win_teased_10,

    -- Teaser push flags
    tl.push_teased_6,
    tl.push_teased_7,
    tl.push_teased_8,
    tl.push_teased_10,

    -- Teased margins
    tl.teased_margin_6,
    tl.teased_margin_7,
    tl.teased_margin_8,
    tl.teased_margin_10,

    -- Flip indicators
    tl.flip_with_6,
    tl.flip_with_7,
    tl.flip_with_8,
    tl.flip_with_10,

    -- Close call indicators
    tl.close_ats_loss,
    tl.blowout_ats_loss,
    tl.teaser_8_squeaker,

    -- =====================================================
    -- DERIVED FEATURE: DATA QUALITY FLAGS
    -- =====================================================
    case
        when sb.games_in_window_20 >= 10 then true
        else false
    end as has_sufficient_history,

    case
        when sb.games_in_window_20 >= 20 then 'full'
        when sb.games_in_window_20 >= 10 then 'moderate'
        when sb.games_in_window_20 >= 5 then 'minimal'
        else 'insufficient'
    end as data_quality_tier

from team_games tg

left join spread_behavior sb
    on tg.game_id = sb.game_id and tg.team_id = sb.team_id

left join total_behavior tb
    on tg.game_id = tb.game_id and tg.team_id = tb.team_id

left join trend_state ts
    on tg.game_id = ts.game_id and tg.team_id = ts.team_id

left join market_profile mp
    on tg.game_id = mp.game_id and tg.team_id = mp.team_id

left join tail_risk tr
    on tg.game_id = tr.game_id and tg.team_id = tr.team_id

left join teaser_labels tl
    on tg.game_id = tl.game_id and tg.team_id = tl.team_id

where tg.closing_spread_team is not null
  and tg.cover_margin_team is not null
