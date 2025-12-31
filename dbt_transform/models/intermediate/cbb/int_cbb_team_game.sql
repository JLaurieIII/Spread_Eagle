{{
    config(
        materialized='view',
        tags=['intermediate', 'cbb']
    )
}}

/*
    TEAM-PERSPECTIVE EXPANSION

    Converts game-level data into team-level rows.
    Each game produces TWO rows: one for home team, one for away team.

    This is CRITICAL for rolling window calculations because
    we need to track each team's sequence of games.

    Key: All metrics are from the TEAM's perspective:
    - team_score, opp_score
    - closing_spread_team (positive = team is underdog)
    - cover_margin_team (positive = team covered)
*/

with outcomes as (
    select * from {{ ref('int_cbb_game_outcomes') }}
),

-- Home team rows
home_rows as (
    select
        -- Keys
        game_id,
        game_date,
        game_date_local,
        season,
        season_type,

        -- Team identification
        home_team_id as team_id,
        home_team as team,
        away_team_id as opponent_id,
        away_team as opponent,
        home_conference as team_conference,
        away_conference as opponent_conference,
        true as is_home,

        -- Game context
        neutral_site,
        conference_game,
        tournament,

        -- Scores (team perspective)
        home_score as team_score,
        away_score as opp_score,
        margin_home as team_margin,  -- positive = team won

        -- Lines (team perspective)
        -- For home team, spread_team = closing_spread_home
        -- If home -5, spread_team = -5 (team favored)
        closing_spread_home as closing_spread_team,
        closing_total,
        opening_spread_home as opening_spread_team,
        opening_total,

        -- Cover margin (team perspective)
        -- cover_margin_team = team_margin + spread_team
        -- If home -5 wins by 3: cover = 3 + (-5) = -2 (didn't cover)
        cover_margin_home as cover_margin_team,

        -- Total metrics (same for both teams)
        total_points,
        total_error,

        -- ATS result (team perspective)
        ats_win_home as ats_win_team,
        ats_push_flag,

        -- O/U result (game level)
        over_win,
        total_push_flag,

        -- Absolute deviations
        abs_cover_margin as abs_cover_margin_team,
        abs_total_error,

        -- Line movement
        spread_movement,
        total_movement,

        -- Moneylines
        home_moneyline as team_moneyline,
        away_moneyline as opp_moneyline

    from outcomes
),

-- Away team rows
away_rows as (
    select
        -- Keys
        game_id,
        game_date,
        game_date_local,
        season,
        season_type,

        -- Team identification (flipped)
        away_team_id as team_id,
        away_team as team,
        home_team_id as opponent_id,
        home_team as opponent,
        away_conference as team_conference,
        home_conference as opponent_conference,
        false as is_home,

        -- Game context
        neutral_site,
        conference_game,
        tournament,

        -- Scores (team perspective - flipped)
        away_score as team_score,
        home_score as opp_score,
        -margin_home as team_margin,  -- flip sign for away

        -- Lines (team perspective)
        -- For away team, spread_team = -closing_spread_home
        -- If home -5, away spread_team = +5 (away is underdog)
        -closing_spread_home as closing_spread_team,
        closing_total,
        -opening_spread_home as opening_spread_team,
        opening_total,

        -- Cover margin (team perspective)
        -- Away team cover = -cover_margin_home
        -- If home didn't cover by 2, away covered by 2
        -cover_margin_home as cover_margin_team,

        -- Total metrics (same for both teams)
        total_points,
        total_error,

        -- ATS result (flipped)
        case
            when ats_win_home = 1 then 0
            when ats_win_home = 0 then 1
            else null
        end as ats_win_team,
        ats_push_flag,

        -- O/U result (game level, same)
        over_win,
        total_push_flag,

        -- Absolute deviations (same)
        abs_cover_margin as abs_cover_margin_team,
        abs_total_error,

        -- Line movement (flipped for away)
        -spread_movement as spread_movement,
        total_movement,

        -- Moneylines (flipped)
        away_moneyline as team_moneyline,
        home_moneyline as opp_moneyline

    from outcomes
),

-- Union both perspectives
combined as (
    select * from home_rows
    union all
    select * from away_rows
),

-- Add row number for ordering (for rolling windows)
sequenced as (
    select
        *,
        row_number() over (
            partition by team_id
            order by game_date, game_id
        ) as team_game_number
    from combined
)

select * from sequenced
