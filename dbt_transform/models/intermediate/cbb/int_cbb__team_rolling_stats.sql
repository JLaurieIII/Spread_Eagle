{{
    config(
        materialized='table'
    )
}}

/*
    ============================================================================
    INTERMEDIATE MODEL: int_cbb__team_rolling_stats
    ============================================================================

    PURPOSE:
    Calculates rolling window statistics for each team's performance metrics.
    These rolling stats capture recent form/trends which are critical predictors
    for total points scoring.

    GRAIN: 1 row per game per team
    - Same grain as int_cbb__team_game_stats
    - Adds rolling window columns (L3, L5, L10 = last 3, 5, 10 games)

    CRITICAL DESIGN DECISIONS:
    1. EXCLUDES CURRENT GAME from all rolling windows
       - Window: ROWS BETWEEN N PRECEDING AND 1 PRECEDING
       - This prevents data leakage in ML training

    2. WITHIN-SEASON ONLY
       - Partitions by (team_id, season)
       - Rolling stats reset at start of each season

    3. ROLLING METRICS CALCULATED:
       - avg_* : Rolling average (central tendency)
       - stddev_* : Rolling standard deviation (consistency/variance)

    USAGE:
    This model is joined to fct_cbb__ml_features_ou for the final feature table.
    ============================================================================
*/

with team_games as (
    select
        game_id,
        team_id,
        season,
        game_date,

        -- Core metrics we'll calculate rolling windows for
        points_scored,
        points_allowed,
        total_points,
        pace,
        possessions,
        offensive_rating,
        defensive_rating,
        net_rating,
        fg_pct,
        fg3_pct,
        ft_pct,
        efg_pct,
        true_shooting_pct,
        offensive_reb_pct,
        turnover_ratio,
        assists,
        steals,
        blocks,
        fastbreak_points,
        paint_points,

        -- Row number for counting games played
        row_number() over (
            partition by team_id, season
            order by game_date, game_id
        ) as season_game_num

    from {{ ref('int_cbb__team_game_stats') }}
),

rolling_calcs as (
    select
        game_id,
        team_id,
        season,
        game_date,
        season_game_num,

        -- =======================================================================
        -- GAMES PLAYED IN EACH WINDOW (for filtering insufficient history)
        -- =======================================================================
        -- Count of games BEFORE this one (excluding current)
        season_game_num - 1 as games_played_season,

        -- =======================================================================
        -- POINTS SCORED - Rolling Stats
        -- =======================================================================
        -- Last 3 games
        avg(points_scored) over w_prev_3 as avg_points_scored_L3,
        stddev_samp(points_scored) over w_prev_3 as stddev_points_scored_L3,

        -- Last 5 games
        avg(points_scored) over w_prev_5 as avg_points_scored_L5,
        stddev_samp(points_scored) over w_prev_5 as stddev_points_scored_L5,

        -- Last 10 games
        avg(points_scored) over w_prev_10 as avg_points_scored_L10,
        stddev_samp(points_scored) over w_prev_10 as stddev_points_scored_L10,

        -- =======================================================================
        -- POINTS ALLOWED - Rolling Stats
        -- =======================================================================
        avg(points_allowed) over w_prev_3 as avg_points_allowed_L3,
        stddev_samp(points_allowed) over w_prev_3 as stddev_points_allowed_L3,

        avg(points_allowed) over w_prev_5 as avg_points_allowed_L5,
        stddev_samp(points_allowed) over w_prev_5 as stddev_points_allowed_L5,

        avg(points_allowed) over w_prev_10 as avg_points_allowed_L10,
        stddev_samp(points_allowed) over w_prev_10 as stddev_points_allowed_L10,

        -- =======================================================================
        -- TOTAL POINTS (scored + allowed) - Rolling Stats
        -- This is the direct predictor for O/U
        -- =======================================================================
        avg(total_points) over w_prev_3 as avg_total_points_L3,
        stddev_samp(total_points) over w_prev_3 as stddev_total_points_L3,

        avg(total_points) over w_prev_5 as avg_total_points_L5,
        stddev_samp(total_points) over w_prev_5 as stddev_total_points_L5,

        avg(total_points) over w_prev_10 as avg_total_points_L10,
        stddev_samp(total_points) over w_prev_10 as stddev_total_points_L10,

        -- =======================================================================
        -- PACE - Rolling Stats (primary driver of total scoring)
        -- =======================================================================
        avg(pace) over w_prev_3 as avg_pace_L3,
        stddev_samp(pace) over w_prev_3 as stddev_pace_L3,

        avg(pace) over w_prev_5 as avg_pace_L5,
        stddev_samp(pace) over w_prev_5 as stddev_pace_L5,

        avg(pace) over w_prev_10 as avg_pace_L10,
        stddev_samp(pace) over w_prev_10 as stddev_pace_L10,

        -- =======================================================================
        -- OFFENSIVE RATING - Rolling Stats
        -- =======================================================================
        avg(offensive_rating) over w_prev_3 as avg_off_rating_L3,
        stddev_samp(offensive_rating) over w_prev_3 as stddev_off_rating_L3,

        avg(offensive_rating) over w_prev_5 as avg_off_rating_L5,
        stddev_samp(offensive_rating) over w_prev_5 as stddev_off_rating_L5,

        avg(offensive_rating) over w_prev_10 as avg_off_rating_L10,
        stddev_samp(offensive_rating) over w_prev_10 as stddev_off_rating_L10,

        -- =======================================================================
        -- DEFENSIVE RATING - Rolling Stats
        -- (lower is better - opponent's offensive rating against this team)
        -- =======================================================================
        avg(defensive_rating) over w_prev_3 as avg_def_rating_L3,
        stddev_samp(defensive_rating) over w_prev_3 as stddev_def_rating_L3,

        avg(defensive_rating) over w_prev_5 as avg_def_rating_L5,
        stddev_samp(defensive_rating) over w_prev_5 as stddev_def_rating_L5,

        avg(defensive_rating) over w_prev_10 as avg_def_rating_L10,
        stddev_samp(defensive_rating) over w_prev_10 as stddev_def_rating_L10,

        -- =======================================================================
        -- NET RATING - Rolling Stats
        -- =======================================================================
        avg(net_rating) over w_prev_5 as avg_net_rating_L5,
        stddev_samp(net_rating) over w_prev_5 as stddev_net_rating_L5,

        avg(net_rating) over w_prev_10 as avg_net_rating_L10,
        stddev_samp(net_rating) over w_prev_10 as stddev_net_rating_L10,

        -- =======================================================================
        -- SHOOTING PERCENTAGES - Rolling Stats
        -- =======================================================================
        -- Field Goal %
        avg(fg_pct) over w_prev_5 as avg_fg_pct_L5,
        stddev_samp(fg_pct) over w_prev_5 as stddev_fg_pct_L5,

        avg(fg_pct) over w_prev_10 as avg_fg_pct_L10,

        -- 3-Point %
        avg(fg3_pct) over w_prev_5 as avg_fg3_pct_L5,
        stddev_samp(fg3_pct) over w_prev_5 as stddev_fg3_pct_L5,

        avg(fg3_pct) over w_prev_10 as avg_fg3_pct_L10,

        -- Free Throw %
        avg(ft_pct) over w_prev_5 as avg_ft_pct_L5,
        avg(ft_pct) over w_prev_10 as avg_ft_pct_L10,

        -- Effective FG%
        avg(efg_pct) over w_prev_5 as avg_efg_pct_L5,
        stddev_samp(efg_pct) over w_prev_5 as stddev_efg_pct_L5,

        avg(efg_pct) over w_prev_10 as avg_efg_pct_L10,

        -- True Shooting %
        avg(true_shooting_pct) over w_prev_5 as avg_true_shooting_L5,
        avg(true_shooting_pct) over w_prev_10 as avg_true_shooting_L10,

        -- =======================================================================
        -- REBOUNDING & TURNOVERS - Rolling Stats
        -- =======================================================================
        avg(offensive_reb_pct) over w_prev_5 as avg_oreb_pct_L5,
        avg(offensive_reb_pct) over w_prev_10 as avg_oreb_pct_L10,

        avg(turnover_ratio) over w_prev_5 as avg_tov_ratio_L5,
        stddev_samp(turnover_ratio) over w_prev_5 as stddev_tov_ratio_L5,

        avg(turnover_ratio) over w_prev_10 as avg_tov_ratio_L10,

        -- =======================================================================
        -- STYLE METRICS - Rolling Stats
        -- =======================================================================
        avg(fastbreak_points) over w_prev_5 as avg_fastbreak_pts_L5,
        avg(paint_points) over w_prev_5 as avg_paint_pts_L5,

        avg(fastbreak_points) over w_prev_10 as avg_fastbreak_pts_L10,
        avg(paint_points) over w_prev_10 as avg_paint_pts_L10

    from team_games
    window
        -- =======================================================================
        -- WINDOW DEFINITIONS
        -- Partitioned by team + season (within-season only)
        -- Ordered by game_date, game_id for deterministic ordering
        -- EXCLUDES current row (ends at 1 PRECEDING)
        -- =======================================================================
        w_prev_3 as (
            partition by team_id, season
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ),
        w_prev_5 as (
            partition by team_id, season
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ),
        w_prev_10 as (
            partition by team_id, season
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        )
)

select * from rolling_calcs
