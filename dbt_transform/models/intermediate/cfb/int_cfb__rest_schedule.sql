{{
    config(
        materialized='table'
    )
}}

/*
    REST & SCHEDULE MODEL (#6)
    
    Grain: 1 row per team per game
    
    Schedule-based features that don't require advanced stats:
    - Days since last game
    - Games in last 7/14 days
    - Back-to-back flags
    - Travel distance (if we add lat/long later)
    
    These are "situation spots" - often exploitable.
*/

with base as (
    select * from {{ ref('int_cfb__game_team_lines') }}
),

with_prev_game as (
    select
        *,
        
        -- Previous game date for this team
        lag(game_date) over (
            partition by team_id 
            order by game_date, game_id
        ) as prev_game_date,
        
        -- Previous game location
        lag(is_home) over (
            partition by team_id 
            order by game_date, game_id
        ) as prev_is_home
        
    from base
),

with_rest as (
    select
        *,
        
        -- Days since last game
        game_date - prev_game_date as days_rest,
        
        -- Rest categories
        case
            when prev_game_date is null then 'season_opener'
            when game_date - prev_game_date <= 4 then 'short_rest'  -- Thurs after Sat
            when game_date - prev_game_date <= 7 then 'normal_rest'
            when game_date - prev_game_date <= 14 then 'extra_rest'  -- Bye week
            else 'long_rest'  -- Bowl prep, etc.
        end as rest_category,
        
        -- Schedule spot flags
        case 
            when game_date - prev_game_date <= 4 then true 
            else false 
        end as is_short_rest,
        
        case 
            when game_date - prev_game_date >= 10 then true 
            else false 
        end as is_off_bye,
        
        -- Travel situation (simplified - home after away, etc.)
        case
            when is_home = true and prev_is_home = false then 'home_after_road'
            when is_home = false and prev_is_home = true then 'road_after_home'
            when is_home = false and prev_is_home = false then 'road_after_road'
            when is_home = true and prev_is_home = true then 'home_after_home'
            else 'unknown'
        end as travel_situation
        
    from with_prev_game
),

-- Add games in recent windows
with_schedule_density as (
    select
        w.*,
        
        -- Count games in last 14 days (including this one)
        (
            select count(*)
            from {{ ref('int_cfb__game_team_lines') }} sub
            where sub.team_id = w.team_id
              and sub.game_date > w.game_date - interval '14 days'
              and sub.game_date <= w.game_date
        ) as games_last_14_days
        
    from with_rest w
)

select * from with_schedule_density
