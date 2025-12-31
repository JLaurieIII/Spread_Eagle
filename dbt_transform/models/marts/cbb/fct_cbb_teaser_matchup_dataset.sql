{{
    config(
        materialized='table',
        tags=['marts', 'cbb', 'ml']
    )
}}

/*
    GAME-LEVEL MATCHUP DATASET FOR TEASERS

    Purpose: One row per game with BOTH teams' features combined.
    Use case: When you want to evaluate a matchup holistically,
    not just one team's perspective.

    Includes:
    - All matchup variance interaction features
    - Both teams' individual features (prefixed home_/away_)
    - Combined metrics (matchup_*)
    - Teaser labels for BOTH teams
*/

with matchup_variance as (
    select * from {{ ref('int_cbb_matchup_variance') }}
),

home_labels as (
    select
        game_id,
        team_id,
        win_teased_6 as home_win_teased_6,
        win_teased_7 as home_win_teased_7,
        win_teased_8 as home_win_teased_8,
        win_teased_10 as home_win_teased_10,
        flip_with_6 as home_flip_with_6,
        flip_with_8 as home_flip_with_8,
        close_ats_loss as home_close_ats_loss,
        blowout_ats_loss as home_blowout_ats_loss
    from {{ ref('int_cbb_teaser_labels') }}
    where is_home = true
),

away_labels as (
    select
        game_id,
        team_id,
        win_teased_6 as away_win_teased_6,
        win_teased_7 as away_win_teased_7,
        win_teased_8 as away_win_teased_8,
        win_teased_10 as away_win_teased_10,
        flip_with_6 as away_flip_with_6,
        flip_with_8 as away_flip_with_8,
        close_ats_loss as away_close_ats_loss,
        blowout_ats_loss as away_blowout_ats_loss
    from {{ ref('int_cbb_teaser_labels') }}
    where is_home = false
)

select
    -- =====================================================
    -- GAME IDENTIFIERS
    -- =====================================================
    mv.game_id,
    mv.game_date,
    mv.season,
    mv.home_team_id,
    mv.home_team,
    mv.away_team_id,
    mv.away_team,

    -- =====================================================
    -- GAME CONTEXT (KNOWN AT BET TIME)
    -- =====================================================
    mv.closing_spread_home,
    mv.closing_total,

    -- =====================================================
    -- ACTUAL OUTCOMES
    -- =====================================================
    mv.cover_margin_home,
    mv.total_error,
    mv.ats_win_home,
    mv.over_win,

    -- =====================================================
    -- HOME TEAM FEATURES
    -- =====================================================
    mv.home_stddev_cover_last5,
    mv.home_stddev_cover_last10,
    mv.home_stddev_cover_last20,
    mv.home_within_7_rate_last10,
    mv.home_within_10_rate_last10,
    mv.home_mean_cover_last10,
    mv.home_tail_8_rate_last10,
    mv.home_tail_10_rate_last10,
    mv.home_tail_15_rate_last10,
    mv.home_teaser_8_survival,
    mv.home_teaser_10_survival,
    mv.home_teaser_risk_tier,
    mv.home_worst_cover_last10,
    mv.home_blowout_rate_last10,
    mv.home_ats_rate_last5,
    mv.home_ats_rate_last10,
    mv.home_ats_streak,
    mv.home_variance_contraction,
    mv.home_ats_hot,
    mv.home_ats_cold,

    -- =====================================================
    -- AWAY TEAM FEATURES
    -- =====================================================
    mv.away_stddev_cover_last5,
    mv.away_stddev_cover_last10,
    mv.away_stddev_cover_last20,
    mv.away_within_7_rate_last10,
    mv.away_within_10_rate_last10,
    mv.away_mean_cover_last10,
    mv.away_tail_8_rate_last10,
    mv.away_tail_10_rate_last10,
    mv.away_tail_15_rate_last10,
    mv.away_teaser_8_survival,
    mv.away_teaser_10_survival,
    mv.away_teaser_risk_tier,
    mv.away_worst_cover_last10,
    mv.away_blowout_rate_last10,
    mv.away_ats_rate_last5,
    mv.away_ats_rate_last10,
    mv.away_ats_streak,
    mv.away_variance_contraction,
    mv.away_ats_hot,
    mv.away_ats_cold,

    -- =====================================================
    -- COMBINED MATCHUP FEATURES
    -- =====================================================
    mv.combined_stddev_cover_last10,
    mv.avg_volatility_last10,
    mv.max_volatility_last10,
    mv.combined_within_7_rate,
    mv.combined_within_10_rate,
    mv.matchup_teaser_8_survival,
    mv.matchup_teaser_10_survival,
    mv.matchup_blowout_risk,
    mv.combined_tail_10_risk,
    mv.teaser_matchup_quality,
    mv.both_teams_stabilizing,
    mv.trend_clash,

    -- =====================================================
    -- HOME TEAM TEASER LABELS
    -- =====================================================
    hl.home_win_teased_6,
    hl.home_win_teased_7,
    hl.home_win_teased_8,
    hl.home_win_teased_10,
    hl.home_flip_with_6,
    hl.home_flip_with_8,
    hl.home_close_ats_loss,
    hl.home_blowout_ats_loss,

    -- =====================================================
    -- AWAY TEAM TEASER LABELS
    -- =====================================================
    al.away_win_teased_6,
    al.away_win_teased_7,
    al.away_win_teased_8,
    al.away_win_teased_10,
    al.away_flip_with_6,
    al.away_flip_with_8,
    al.away_close_ats_loss,
    al.away_blowout_ats_loss,

    -- =====================================================
    -- PARLAY-STYLE COMBINED LABELS
    -- Both teams must win their teaser for parlay success
    -- =====================================================
    case
        when hl.home_win_teased_8 = 1 and al.away_win_teased_8 = 1 then 1
        when hl.home_win_teased_8 = 0 or al.away_win_teased_8 = 0 then 0
        else null
    end as both_teams_win_teased_8,

    case
        when hl.home_win_teased_10 = 1 and al.away_win_teased_10 = 1 then 1
        when hl.home_win_teased_10 = 0 or al.away_win_teased_10 = 0 then 0
        else null
    end as both_teams_win_teased_10

from matchup_variance mv

left join home_labels hl
    on mv.game_id = hl.game_id and mv.home_team_id = hl.team_id

left join away_labels al
    on mv.game_id = al.game_id and mv.away_team_id = al.team_id

where mv.closing_spread_home is not null
  and mv.cover_margin_home is not null
