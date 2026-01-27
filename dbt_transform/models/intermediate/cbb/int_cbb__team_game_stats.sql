{{
    config(
        materialized='view'
    )
}}

/*
    ============================================================================
    INTERMEDIATE MODEL: int_cbb__team_game_stats
    ============================================================================

    PURPOSE:
    Cleans and normalizes per-game team statistics into a consistent format
    for downstream rolling window calculations and ML feature engineering.

    GRAIN: 1 row per game per team
    - Each game appears twice (once for each team's perspective)
    - team_id is the team whose stats are in the ts_* columns
    - opponent_id is the opposing team

    SOURCE: cbb.game_team_stats (raw table)

    RAW COLUMN NAMING CONVENTION:
    - ts_* = team stats (the team in this row)
    - os_* = opponent stats (the opposing team)
    - ts_2pt_*, ts_3pt_* for 2-point and 3-point field goals
    - ts_fg_* for overall field goals

    ============================================================================
*/

with source as (
    -- Use staging to keep column naming and date parsing consistent
    select * from {{ ref('stg_cbb__game_team_stats') }}
),

cleaned as (
    select
        -- =======================================================================
        -- IDENTIFIERS
        -- =======================================================================
        game_id,
        team_id,
        opponent_id,
        season,
        season_label,
        season_type,
        game_date,

        -- =======================================================================
        -- GAME CONTEXT
        -- =======================================================================
        is_home,
        neutral_site,
        conference_game,
        tournament,
        game_type,

        -- Team metadata (for joins/debugging)
        team,
        conference,
        opponent,

        -- =======================================================================
        -- CORE SCORING
        -- ts_points_total = points scored by this team
        -- os_points_total = points scored by opponent (allowed by this team)
        -- =======================================================================
        team_stats_points_total as points_scored,
        opponent_stats_points_total as points_allowed,
        team_stats_points_total + opponent_stats_points_total as total_points,

        -- =======================================================================
        -- PACE & POSSESSIONS (key driver of total scoring)
        -- =======================================================================
        pace,
        team_stats_possessions as possessions,
        game_minutes,

        -- =======================================================================
        -- EFFICIENCY RATINGS (points per 100 possessions)
        -- ts_rating = team's offensive efficiency
        -- os_rating = opponent's offensive efficiency (= team's defensive efficiency)
        -- =======================================================================
        team_stats_rating as offensive_rating,
        opponent_stats_rating as defensive_rating,
        team_stats_rating - opponent_stats_rating as net_rating,

        -- =======================================================================
        -- SHOOTING PERCENTAGES
        -- Note: Raw table uses team_stats_* naming (already snake_cased)
        -- =======================================================================
        -- Overall Field Goals
        team_stats_field_goals_pct as fg_pct,
        team_stats_field_goals_made as fg_made,
        team_stats_field_goals_attempted as fg_attempted,

        -- Two-Point Field Goals
        team_stats_two_point_field_goals_pct as fg2_pct,
        team_stats_two_point_field_goals_made as fg2_made,
        team_stats_two_point_field_goals_attempted as fg2_attempted,

        -- Three-Point Field Goals
        team_stats_three_point_field_goals_pct as fg3_pct,
        team_stats_three_point_field_goals_made as fg3_made,
        team_stats_three_point_field_goals_attempted as fg3_attempted,

        -- Free Throws
        team_stats_free_throws_pct as ft_pct,
        team_stats_free_throws_made as ft_made,
        team_stats_free_throws_attempted as ft_attempted,

        -- Advanced Shooting
        team_stats_four_factors_effective_field_goal_pct as efg_pct,
        team_stats_true_shooting as true_shooting_pct,
        team_stats_four_factors_free_throw_rate as ft_rate,

        -- =======================================================================
        -- REBOUNDING
        -- =======================================================================
        team_stats_rebounds_offensive as offensive_rebounds,
        team_stats_rebounds_defensive as defensive_rebounds,
        team_stats_rebounds_total as total_rebounds,
        team_stats_four_factors_offensive_rebound_pct as offensive_reb_pct,

        -- =======================================================================
        -- TURNOVERS
        -- =======================================================================
        team_stats_turnovers_total as turnovers,
        team_stats_four_factors_turnover_ratio as turnover_ratio,

        -- =======================================================================
        -- OTHER COUNTING STATS
        -- =======================================================================
        team_stats_assists as assists,
        team_stats_steals as steals,
        team_stats_blocks as blocks,
        team_stats_fouls_total as fouls,

        -- =======================================================================
        -- SCORING BREAKDOWN
        -- =======================================================================
        team_stats_points_fast_break as fastbreak_points,
        team_stats_points_in_paint as paint_points,
        team_stats_points_off_turnovers as points_off_turnovers,
        team_stats_points_largest_lead as largest_lead,

        -- =======================================================================
        -- OPPONENT STATS (for matchup analysis)
        -- =======================================================================
        opponent_stats_field_goals_pct as opp_fg_pct,
        opponent_stats_three_point_field_goals_pct as opp_fg3_pct,
        opponent_stats_four_factors_effective_field_goal_pct as opp_efg_pct,
        opponent_stats_four_factors_turnover_ratio as opp_turnover_ratio,
        opponent_stats_four_factors_offensive_rebound_pct as opp_offensive_reb_pct,

        -- =======================================================================
        -- GAME QUALITY METRICS
        -- =======================================================================
        team_stats_game_score as game_score

    from source
    where
        -- Only completed games with valid stats
        team_stats_points_total is not null
        and opponent_stats_points_total is not null
        and pace is not null
)

select * from cleaned
