{{
    config(
        materialized='table'
    )
}}

/*
    ============================================================================
    FACT MODEL: fct_cbb__teaser_matchups
    ============================================================================

    PURPOSE:
    Final ML-ready table for teaser betting strategy.
    Combines both teams' volatility metrics to identify "safe" teaser games.

    STRATEGY:
    Find games where BOTH teams have:
    - High historical teaser survival rates
    - Low cover margin volatility
    - Few blowout losses

    GRAIN: 1 row per game (from home team perspective)

    OUTPUT:
    - Home team volatility metrics
    - Away team volatility metrics
    - Combined matchup quality scores
    - Target: both_teams_teaser_8_win, both_teams_teaser_10_win

    ============================================================================
*/

with home_volatility as (
    select * from {{ ref('int_cbb__team_spread_volatility') }}
    where is_home = true
),

away_volatility as (
    select * from {{ ref('int_cbb__team_spread_volatility') }}
    where is_home = false
),

matchups as (
    select
        h.game_id,
        h.game_date,
        h.season,

        -- =======================================================================
        -- TEAMS
        -- =======================================================================
        h.team_id as home_id,
        h.team_name as home_team,
        a.team_id as away_id,
        a.team_name as away_team,

        -- =======================================================================
        -- GAME CONTEXT
        -- =======================================================================
        h.spread_faced as home_spread,
        h.point_margin as home_margin,
        h.cover_margin as home_cover_margin,

        -- =======================================================================
        -- HOME TEAM VOLATILITY (prefix: home_)
        -- =======================================================================
        h.games_played as home_games_played,
        h.stddev_cover_margin_l5 as home_stddev_cover_l5,
        h.stddev_cover_margin_l10 as home_stddev_cover_l10,
        h.within_7_rate_l10 as home_within_7_rate,
        h.within_10_rate_l10 as home_within_10_rate,
        h.teaser_8_survival_l5 as home_teaser_8_surv_l5,
        h.teaser_8_survival_l10 as home_teaser_8_surv_l10,
        h.teaser_10_survival_l5 as home_teaser_10_surv_l5,
        h.teaser_10_survival_l10 as home_teaser_10_surv_l10,
        h.blowout_rate_l10 as home_blowout_rate,
        h.worst_cover_l10 as home_worst_cover,
        h.ats_win_rate_l10 as home_ats_rate,

        -- =======================================================================
        -- AWAY TEAM VOLATILITY (prefix: away_)
        -- =======================================================================
        a.games_played as away_games_played,
        a.stddev_cover_margin_l5 as away_stddev_cover_l5,
        a.stddev_cover_margin_l10 as away_stddev_cover_l10,
        a.within_7_rate_l10 as away_within_7_rate,
        a.within_10_rate_l10 as away_within_10_rate,
        a.teaser_8_survival_l5 as away_teaser_8_surv_l5,
        a.teaser_8_survival_l10 as away_teaser_8_surv_l10,
        a.teaser_10_survival_l5 as away_teaser_10_surv_l5,
        a.teaser_10_survival_l10 as away_teaser_10_surv_l10,
        a.blowout_rate_l10 as away_blowout_rate,
        a.worst_cover_l10 as away_worst_cover,
        a.ats_win_rate_l10 as away_ats_rate,

        -- =======================================================================
        -- COMBINED MATCHUP METRICS
        -- =======================================================================
        -- Combined volatility (lower = more predictable matchup)
        (coalesce(h.stddev_cover_margin_l10, 15) + coalesce(a.stddev_cover_margin_l10, 15)) / 2.0
            as combined_stddev_cover,

        -- Combined teaser survival expectation
        (coalesce(h.teaser_8_survival_l10, 0.75) + coalesce(a.teaser_8_survival_l10, 0.75)) / 2.0
            as combined_teaser_8_survival,
        (coalesce(h.teaser_10_survival_l10, 0.80) + coalesce(a.teaser_10_survival_l10, 0.80)) / 2.0
            as combined_teaser_10_survival,

        -- Combined close game rate
        (coalesce(h.within_10_rate_l10, 0.6) + coalesce(a.within_10_rate_l10, 0.6)) / 2.0
            as combined_within_10_rate,

        -- Combined blowout risk (lower = safer)
        (coalesce(h.blowout_rate_l10, 0.1) + coalesce(a.blowout_rate_l10, 0.1)) / 2.0
            as combined_blowout_rate,

        -- Worst case from either team
        least(coalesce(h.worst_cover_l10, -20), coalesce(a.worst_cover_l10, -20))
            as worst_cover_either_team,

        -- =======================================================================
        -- TARGET VARIABLES (actual outcomes)
        -- =======================================================================
        h.teaser_8_win as home_teaser_8_win,
        h.teaser_10_win as home_teaser_10_win,
        a.teaser_8_win as away_teaser_8_win,
        a.teaser_10_win as away_teaser_10_win,

        -- Both teams survive teaser (for parlay logic)
        case
            when h.teaser_8_win = 1 and a.teaser_8_win = 1 then 1
            else 0
        end as both_teams_teaser_8_win,

        case
            when h.teaser_10_win = 1 and a.teaser_10_win = 1 then 1
            else 0
        end as both_teams_teaser_10_win,

        -- =======================================================================
        -- FILTER FLAGS
        -- =======================================================================
        case
            when h.games_played >= 5 and a.games_played >= 5 then true
            else false
        end as has_sufficient_history,

        case
            when h.games_played >= 10 and a.games_played >= 10 then true
            else false
        end as has_full_history,

        -- Is this a completed game (for training) or upcoming (for prediction)?
        case
            when h.cover_margin is not null then true
            else false
        end as is_completed

    from home_volatility h
    inner join away_volatility a
        on h.game_id = a.game_id
)

select * from matchups
order by game_date desc, game_id
