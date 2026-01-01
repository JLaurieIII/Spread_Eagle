{{
    config(
        materialized='table'
    )
}}

/*
    LINE MOVEMENT MODEL (#7)
    
    Grain: 1 row per team per game
    
    Market behavior features:
    - Spread movement (open to close)
    - Total movement
    - Steam move detection
    - Closing line value indicators
    
    Line movement often signals sharp money or injury news.
*/

with lines as (
    select * from {{ ref('stg_cfb__betting_lines') }}
),

games as (
    select * from {{ ref('int_cfb__game_team_lines') }}
),

-- Aggregate line info per game (handle multiple providers)
game_lines as (
    select
        game_id,
        
        -- Use average across providers for more stable signal
        avg(spread_open) as spread_open_avg,
        avg(spread_close) as spread_close_avg,
        avg(spread_close) - avg(spread_open) as spread_movement,
        
        avg(total_open) as total_open_avg,
        avg(total_close) as total_close_avg,
        avg(total_close) - avg(total_open) as total_movement,
        
        -- Movement magnitude
        abs(avg(spread_close) - avg(spread_open)) as spread_move_abs,
        abs(avg(total_close) - avg(total_open)) as total_move_abs
        
    from lines
    where spread_open is not null
    group by game_id
),

-- Join with team-game data
final as (
    select
        g.sport,
        g.game_id,
        g.season,
        g.week,
        g.game_date,
        g.team_id,
        g.team_name,
        g.opponent_name,
        g.is_home,
        
        -- Current spread/total
        g.spread_close_for_team,
        g.total_close,
        
        -- Line movement (from game perspective, adjusted for team)
        case 
            when g.is_home then l.spread_movement
            else -1 * l.spread_movement
        end as spread_movement_for_team,
        l.total_movement,
        
        -- Steam move flags (significant movement)
        case 
            when l.spread_move_abs >= 2.0 then true 
            else false 
        end as is_spread_steam_move,
        
        case 
            when l.total_move_abs >= 3.0 then true 
            else false 
        end as is_total_steam_move,
        
        -- Direction of movement
        case
            when g.is_home and l.spread_movement < -0.5 then 'moved_toward_home'
            when g.is_home and l.spread_movement > 0.5 then 'moved_toward_away'
            when not g.is_home and l.spread_movement > 0.5 then 'moved_toward_team'
            when not g.is_home and l.spread_movement < -0.5 then 'moved_against_team'
            else 'stable'
        end as spread_move_direction,
        
        -- Outcome (did the closing line side win ATS?)
        g.is_cover,
        g.ats_margin
        
    from games g
    left join game_lines l on g.game_id = l.game_id
)

select * from final
