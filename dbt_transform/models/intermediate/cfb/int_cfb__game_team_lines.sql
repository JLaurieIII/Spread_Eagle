{{
    config(
        materialized='table'
    )
}}

/*
    FOUNDATION MODEL: Game-Team-Lines
    
    Grain: 1 row per team per game (2 rows per game)
    
    This is THE core table for all ATS/OU analysis.
    Every other model builds on this.
    
    Key transformations:
    - Unpivot home/away to team perspective
    - Normalize spread to team's perspective (positive = underdog)
    - Calculate all margin metrics (score, ATS, OU)
    - Flag covers, pushes, overs
*/

with games as (
    select * from {{ ref('stg_cfb__games') }}
),

lines as (
    -- Aggregate across providers for a deterministic, stable line per game
    select
        game_id,
        avg(spread_close) as spread_close,
        avg(spread_open) as spread_open,
        avg(spread_close) - avg(spread_open) as spread_movement,
        avg(total_close) as total_close,
        avg(total_open) as total_open,
        avg(total_close) - avg(total_open) as total_movement
    from {{ ref('stg_cfb__betting_lines') }}
    where spread_close is not null
    group by game_id
),

-- Unpivot: Create one row per team per game
team_games as (
    -- HOME team perspective
    select
        'cfb' as sport,
        g.game_id,
        g.season,
        g.week,
        g.game_date,
        g.is_neutral_site,
        g.is_conference_game,
        
        -- Team identifiers
        g.home_id as team_id,
        g.home_team as team_name,
        g.away_id as opponent_id,
        g.away_team as opponent_name,
        true as is_home,
        
        -- Scores
        g.home_points as team_points,
        g.away_points as opponent_points,
        
        -- Spread from THIS team's perspective
        -- Raw spread is home perspective (negative = home favored)
        -- For home team: keep as-is
        l.spread_close as spread_close_for_team,
        l.spread_open as spread_open_for_team,
        
        -- Total
        l.total_close,
        l.total_open
        
    from games g
    left join lines l on g.game_id = l.game_id
    
    union all
    
    -- AWAY team perspective
    select
        'cfb' as sport,
        g.game_id,
        g.season,
        g.week,
        g.game_date,
        g.is_neutral_site,
        g.is_conference_game,
        
        -- Team identifiers (flipped)
        g.away_id as team_id,
        g.away_team as team_name,
        g.home_id as opponent_id,
        g.home_team as opponent_name,
        false as is_home,
        
        -- Scores
        g.away_points as team_points,
        g.home_points as opponent_points,
        
        -- Spread from THIS team's perspective
        -- For away team: flip the sign
        -1 * l.spread_close as spread_close_for_team,
        -1 * l.spread_open as spread_open_for_team,
        
        -- Total (same for both sides)
        l.total_close,
        l.total_open
        
    from games g
    left join lines l on g.game_id = l.game_id
),

-- Calculate all the margins and flags
with_margins as (
    select
        *,
        
        -- Score margin (positive = team won)
        team_points - opponent_points as score_margin,
        
        -- ATS margin (positive = team covered)
        -- spread_close_for_team is positive for underdogs
        -- If team is +7 and wins by 3, they covered: -3 + 7 = +4 ATS margin
        (team_points - opponent_points) + spread_close_for_team as ats_margin,
        
        -- O/U margin (positive = went over)
        (team_points + opponent_points) - total_close as ou_margin,
        
        -- Total points in game
        team_points + opponent_points as total_points
        
    from team_games
    where team_points is not null  -- Only completed games with scores
      and spread_close_for_team is not null  -- Must have a line
),

-- Add boolean flags
final as (
    select
        *,
        
        -- ATS flags
        case 
            when ats_margin > 0 then true
            when ats_margin < 0 then false
            else null  -- push
        end as is_cover,
        
        case when ats_margin = 0 then true else false end as is_push_ats,
        
        -- O/U flags  
        case
            when ou_margin > 0 then true
            when ou_margin < 0 then false
            else null  -- push
        end as is_over,
        
        case when ou_margin = 0 then true else false end as is_push_ou,
        
        -- Win flag
        case
            when score_margin > 0 then true
            when score_margin < 0 then false
            else null  -- tie
        end as is_win
        
    from with_margins
)

select * from final
order by game_date, game_id, is_home desc
