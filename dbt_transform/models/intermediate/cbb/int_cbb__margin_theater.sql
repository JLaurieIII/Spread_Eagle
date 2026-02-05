{{
    config(
        materialized='table'
    )
}}

/*
    ============================================================================
    INTERMEDIATE MODEL: int_cbb__margin_theater
    ============================================================================

    PURPOSE:
    Unified margin data with full situational context for the "Margin Theater"
    interactive filtering feature. Supports filtering distributions by:
    - Role (favorite/underdog)
    - Venue (home/away)
    - Game type (conference/non-conference)
    - Momentum (after win/loss)
    - Rest days (0, 1, 2+)

    GRAIN: 1 row per team per game (completed games with Bovada lines only)

    SOURCES:
    - cbb.betting_lines (Bovada provider)
    - cbb.games (for conference_game flag)

    ============================================================================
*/

with bovada_games as (
    -- Base: all completed Bovada games with both spread and total
    select
        bl.game_id,
        {{ eastern_date('bl.start_date') }} as game_date,
        bl.season,
        bl.home_team_id,
        bl.home_team,
        bl.away_team_id,
        bl.away_team,
        bl.home_score,
        bl.away_score,
        bl.spread,
        bl.over_under as vegas_total,
        g.conference_game as is_conference_game
    from cbb.betting_lines bl
    inner join cbb.games g on bl.game_id = g.id
    where bl.provider = 'Bovada'
      and bl.home_score is not null
      and bl.home_score > 0
      and bl.spread is not null
      and bl.over_under is not null
),

team_game_margins as (
    -- Expand to team perspective (one row per team per game)

    -- Home team perspective
    select
        game_id,
        game_date,
        season,
        home_team_id as team_id,
        home_team as team_name,
        true as is_home,
        is_conference_game,
        -- Spread metrics
        spread as spread_faced,  -- negative = favorite
        spread < 0 as is_favorite,
        (home_score - away_score) as point_margin,
        (home_score - away_score) + spread as cover_margin,
        -- Total metrics
        vegas_total,
        (home_score + away_score) as actual_total,
        (home_score + away_score) - vegas_total as total_margin
    from bovada_games

    union all

    -- Away team perspective
    select
        game_id,
        game_date,
        season,
        away_team_id as team_id,
        away_team as team_name,
        false as is_home,
        is_conference_game,
        -- Spread metrics (flip spread for away team)
        -spread as spread_faced,
        -spread < 0 as is_favorite,
        (away_score - home_score) as point_margin,
        (away_score - home_score) + (-spread) as cover_margin,
        -- Total metrics (same for both teams)
        vegas_total,
        (home_score + away_score) as actual_total,
        (home_score + away_score) - vegas_total as total_margin
    from bovada_games
),

with_situational_context as (
    -- Add lagged context (previous result, rest days)
    select
        *,
        -- Previous game result for this team
        lag(
            case when point_margin > 0 then 'W' else 'L' end
        ) over (
            partition by team_id, season
            order by game_date, game_id
        ) as prev_game_result,

        -- Days since previous game
        (game_date - lag(game_date) over (
            partition by team_id, season
            order by game_date, game_id
        ))::int as rest_days,

        -- Game number in season (for debugging/validation)
        row_number() over (
            partition by team_id, season
            order by game_date, game_id
        ) as season_game_num

    from team_game_margins
)

select
    game_id,
    game_date,
    season,
    team_id,
    team_name,
    season_game_num,

    -- Spread data
    cover_margin,
    spread_faced,
    is_favorite,

    -- Total data
    total_margin,
    vegas_total,
    actual_total,

    -- Situational filters
    is_home,
    is_conference_game,
    prev_game_result,
    rest_days

from with_situational_context
order by game_date desc, game_id, team_id
