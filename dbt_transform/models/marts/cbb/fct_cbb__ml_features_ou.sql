{{
    config(
        materialized='table'
    )
}}

/*
    ============================================================================
    FACT MODEL: fct_cbb__ml_features_ou
    ============================================================================

    PURPOSE:
    Final ML-ready feature table for predicting college basketball game totals
    (Over/Under). Contains all features needed to train models that predict:
    1. Expected total points
    2. Probability distribution over possible totals
    3. P(Over) at the Vegas line

    GRAIN: 1 row per game
    - Only games with Bovada O/U lines
    - Includes both historical (completed) and future (scheduled) games

    FEATURE CATEGORIES:
    1. Home team rolling stats (prefix: home_*)
    2. Away team rolling stats (prefix: away_*)
    3. Combined/derived features (prefix: combined_* or diff_*)
    4. Vegas line features
    5. Target variables (for completed games)
    6. Filter flags for data quality

    ML TRAINING NOTES:
    - Filter to has_sufficient_history = true for training
    - Filter to is_completed = true for training (has actual outcomes)
    - Use vegas_total as a feature (market expectation)
    - Target: actual_total (regression) or over_hit (classification)

    ============================================================================
*/

with betting as (
    select * from {{ ref('int_cbb__game_betting_outcomes') }}
),

home_rolling as (
    select * from {{ ref('int_cbb__team_rolling_stats') }}
),

away_rolling as (
    select * from {{ ref('int_cbb__team_rolling_stats') }}
),

-- Get current game stats for the home team (for reference/debugging)
home_game_stats as (
    select
        game_id,
        team_id,
        points_scored,
        points_allowed,
        pace as game_pace,
        offensive_rating as game_off_rating,
        defensive_rating as game_def_rating
    from {{ ref('int_cbb__team_game_stats') }}
),

-- Get current game stats for the away team
away_game_stats as (
    select
        game_id,
        team_id,
        points_scored,
        points_allowed,
        pace as game_pace,
        offensive_rating as game_off_rating,
        defensive_rating as game_def_rating
    from {{ ref('int_cbb__team_game_stats') }}
),

features as (
    select
        -- =======================================================================
        -- GAME IDENTIFIERS & METADATA
        -- =======================================================================
        b.game_id,
        b.game_date,
        b.game_timestamp,
        b.season,
        b.season_type,
        b.is_neutral_site,
        b.is_conference_game,
        b.tournament,

        -- Teams
        b.home_id,
        b.home_team,
        b.home_conference,
        b.away_id,
        b.away_team,
        b.away_conference,

        -- =======================================================================
        -- VEGAS LINE FEATURES
        -- These are known before the game and are strong predictors
        -- =======================================================================
        b.vegas_total,
        b.vegas_total_open,
        b.vegas_line_movement,
        b.vegas_spread,

        -- =======================================================================
        -- HOME TEAM ROLLING FEATURES (from int_cbb__team_rolling_stats)
        -- =======================================================================
        hr.games_played_season as home_games_played,

        -- Points Scored
        hr.avg_points_scored_L3 as home_avg_pts_scored_L3,
        hr.avg_points_scored_L5 as home_avg_pts_scored_L5,
        hr.avg_points_scored_L10 as home_avg_pts_scored_L10,
        hr.stddev_points_scored_L5 as home_stddev_pts_scored_L5,
        hr.stddev_points_scored_L10 as home_stddev_pts_scored_L10,

        -- Points Allowed
        hr.avg_points_allowed_L3 as home_avg_pts_allowed_L3,
        hr.avg_points_allowed_L5 as home_avg_pts_allowed_L5,
        hr.avg_points_allowed_L10 as home_avg_pts_allowed_L10,
        hr.stddev_points_allowed_L5 as home_stddev_pts_allowed_L5,
        hr.stddev_points_allowed_L10 as home_stddev_pts_allowed_L10,

        -- Total Points (from team's games)
        hr.avg_total_points_L3 as home_avg_total_pts_L3,
        hr.avg_total_points_L5 as home_avg_total_pts_L5,
        hr.avg_total_points_L10 as home_avg_total_pts_L10,
        hr.stddev_total_points_L5 as home_stddev_total_pts_L5,
        hr.stddev_total_points_L10 as home_stddev_total_pts_L10,

        -- Pace
        hr.avg_pace_L3 as home_avg_pace_L3,
        hr.avg_pace_L5 as home_avg_pace_L5,
        hr.avg_pace_L10 as home_avg_pace_L10,
        hr.stddev_pace_L5 as home_stddev_pace_L5,

        -- Efficiency
        hr.avg_off_rating_L5 as home_avg_off_rating_L5,
        hr.avg_off_rating_L10 as home_avg_off_rating_L10,
        hr.stddev_off_rating_L5 as home_stddev_off_rating_L5,
        hr.avg_def_rating_L5 as home_avg_def_rating_L5,
        hr.avg_def_rating_L10 as home_avg_def_rating_L10,
        hr.stddev_def_rating_L5 as home_stddev_def_rating_L5,
        hr.avg_net_rating_L5 as home_avg_net_rating_L5,
        hr.avg_net_rating_L10 as home_avg_net_rating_L10,

        -- Shooting
        hr.avg_fg_pct_L5 as home_avg_fg_pct_L5,
        hr.avg_fg_pct_L10 as home_avg_fg_pct_L10,
        hr.avg_fg3_pct_L5 as home_avg_fg3_pct_L5,
        hr.avg_fg3_pct_L10 as home_avg_fg3_pct_L10,
        hr.avg_efg_pct_L5 as home_avg_efg_pct_L5,
        hr.avg_efg_pct_L10 as home_avg_efg_pct_L10,
        hr.avg_true_shooting_L5 as home_avg_ts_pct_L5,
        hr.avg_ft_pct_L5 as home_avg_ft_pct_L5,

        -- Rebounding & Turnovers
        hr.avg_oreb_pct_L5 as home_avg_oreb_pct_L5,
        hr.avg_oreb_pct_L10 as home_avg_oreb_pct_L10,
        hr.avg_tov_ratio_L5 as home_avg_tov_ratio_L5,
        hr.avg_tov_ratio_L10 as home_avg_tov_ratio_L10,
        hr.stddev_tov_ratio_L5 as home_stddev_tov_ratio_L5,

        -- Style
        hr.avg_fastbreak_pts_L5 as home_avg_fastbreak_L5,
        hr.avg_paint_pts_L5 as home_avg_paint_pts_L5,

        -- =======================================================================
        -- AWAY TEAM ROLLING FEATURES
        -- =======================================================================
        ar.games_played_season as away_games_played,

        -- Points Scored
        ar.avg_points_scored_L3 as away_avg_pts_scored_L3,
        ar.avg_points_scored_L5 as away_avg_pts_scored_L5,
        ar.avg_points_scored_L10 as away_avg_pts_scored_L10,
        ar.stddev_points_scored_L5 as away_stddev_pts_scored_L5,
        ar.stddev_points_scored_L10 as away_stddev_pts_scored_L10,

        -- Points Allowed
        ar.avg_points_allowed_L3 as away_avg_pts_allowed_L3,
        ar.avg_points_allowed_L5 as away_avg_pts_allowed_L5,
        ar.avg_points_allowed_L10 as away_avg_pts_allowed_L10,
        ar.stddev_points_allowed_L5 as away_stddev_pts_allowed_L5,
        ar.stddev_points_allowed_L10 as away_stddev_pts_allowed_L10,

        -- Total Points
        ar.avg_total_points_L3 as away_avg_total_pts_L3,
        ar.avg_total_points_L5 as away_avg_total_pts_L5,
        ar.avg_total_points_L10 as away_avg_total_pts_L10,
        ar.stddev_total_points_L5 as away_stddev_total_pts_L5,
        ar.stddev_total_points_L10 as away_stddev_total_pts_L10,

        -- Pace
        ar.avg_pace_L3 as away_avg_pace_L3,
        ar.avg_pace_L5 as away_avg_pace_L5,
        ar.avg_pace_L10 as away_avg_pace_L10,
        ar.stddev_pace_L5 as away_stddev_pace_L5,

        -- Efficiency
        ar.avg_off_rating_L5 as away_avg_off_rating_L5,
        ar.avg_off_rating_L10 as away_avg_off_rating_L10,
        ar.stddev_off_rating_L5 as away_stddev_off_rating_L5,
        ar.avg_def_rating_L5 as away_avg_def_rating_L5,
        ar.avg_def_rating_L10 as away_avg_def_rating_L10,
        ar.stddev_def_rating_L5 as away_stddev_def_rating_L5,
        ar.avg_net_rating_L5 as away_avg_net_rating_L5,
        ar.avg_net_rating_L10 as away_avg_net_rating_L10,

        -- Shooting
        ar.avg_fg_pct_L5 as away_avg_fg_pct_L5,
        ar.avg_fg_pct_L10 as away_avg_fg_pct_L10,
        ar.avg_fg3_pct_L5 as away_avg_fg3_pct_L5,
        ar.avg_fg3_pct_L10 as away_avg_fg3_pct_L10,
        ar.avg_efg_pct_L5 as away_avg_efg_pct_L5,
        ar.avg_efg_pct_L10 as away_avg_efg_pct_L10,
        ar.avg_true_shooting_L5 as away_avg_ts_pct_L5,
        ar.avg_ft_pct_L5 as away_avg_ft_pct_L5,

        -- Rebounding & Turnovers
        ar.avg_oreb_pct_L5 as away_avg_oreb_pct_L5,
        ar.avg_oreb_pct_L10 as away_avg_oreb_pct_L10,
        ar.avg_tov_ratio_L5 as away_avg_tov_ratio_L5,
        ar.avg_tov_ratio_L10 as away_avg_tov_ratio_L10,
        ar.stddev_tov_ratio_L5 as away_stddev_tov_ratio_L5,

        -- Style
        ar.avg_fastbreak_pts_L5 as away_avg_fastbreak_L5,
        ar.avg_paint_pts_L5 as away_avg_paint_pts_L5,

        -- =======================================================================
        -- COMBINED / DERIVED FEATURES
        -- These combine home + away metrics for direct O/U prediction
        -- =======================================================================

        -- Combined Average Total Points (most direct predictor)
        -- Sum of each team's average total points from their games
        (hr.avg_total_points_L5 + ar.avg_total_points_L5) / 2.0 as combined_avg_total_L5,
        (hr.avg_total_points_L10 + ar.avg_total_points_L10) / 2.0 as combined_avg_total_L10,

        -- Combined Pace (higher pace = more possessions = more scoring)
        (hr.avg_pace_L5 + ar.avg_pace_L5) / 2.0 as combined_avg_pace_L5,
        (hr.avg_pace_L10 + ar.avg_pace_L10) / 2.0 as combined_avg_pace_L10,

        -- Expected Points: Home Off vs Away Def + Away Off vs Home Def
        -- This estimates total based on efficiency matchups
        (hr.avg_off_rating_L5 + ar.avg_off_rating_L5) / 2.0 as combined_avg_off_rating_L5,
        (hr.avg_def_rating_L5 + ar.avg_def_rating_L5) / 2.0 as combined_avg_def_rating_L5,

        -- Efficiency differential (positive = higher scoring expected)
        (hr.avg_off_rating_L5 - ar.avg_def_rating_L5) as home_off_vs_away_def_L5,
        (ar.avg_off_rating_L5 - hr.avg_def_rating_L5) as away_off_vs_home_def_L5,

        -- Combined shooting
        (hr.avg_efg_pct_L5 + ar.avg_efg_pct_L5) / 2.0 as combined_avg_efg_L5,

        -- Variance indicators (higher variance = less predictable)
        (coalesce(hr.stddev_total_points_L5, 0) + coalesce(ar.stddev_total_points_L5, 0)) / 2.0 as combined_stddev_total_L5,
        (coalesce(hr.stddev_pace_L5, 0) + coalesce(ar.stddev_pace_L5, 0)) / 2.0 as combined_stddev_pace_L5,

        -- =======================================================================
        -- TARGET VARIABLES (for completed games only)
        -- =======================================================================
        b.home_points,
        b.away_points,
        b.actual_total,
        b.total_margin,
        b.total_margin_abs,
        b.ou_result,
        b.over_hit,
        b.is_push,

        -- =======================================================================
        -- FILTER FLAGS
        -- =======================================================================
        -- Game is completed (has actual results)
        case when b.actual_total is not null then true else false end as is_completed,

        -- Both teams have sufficient history for reliable rolling stats
        -- Require at least 5 games for L5 windows to be meaningful
        case
            when hr.games_played_season >= 5 and ar.games_played_season >= 5
            then true
            else false
        end as has_sufficient_history,

        -- Minimum 3 games for basic features
        case
            when hr.games_played_season >= 3 and ar.games_played_season >= 3
            then true
            else false
        end as has_minimum_history

    from betting b
    -- Join home team's rolling stats
    left join home_rolling hr
        on b.game_id = hr.game_id
        and b.home_id = hr.team_id
    -- Join away team's rolling stats
    left join away_rolling ar
        on b.game_id = ar.game_id
        and b.away_id = ar.team_id
)

select * from features
order by game_date desc, game_id
