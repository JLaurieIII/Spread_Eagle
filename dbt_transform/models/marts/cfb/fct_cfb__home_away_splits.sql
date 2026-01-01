{{
    config(
        materialized='table'
    )
}}

/*
    HOME/AWAY SPLITS MODEL (#5)
    
    Grain: 1 row per team per season (or rolling)
    
    Location-based performance splits.
    Football has significant home field advantage.
    
    Useful for:
    - Adjusting predictions based on location
    - Finding teams that underperform on the road
    - Identifying "road warrior" teams
*/

with base as (
    select * from {{ ref('int_cfb__game_team_lines') }}
),

-- Calculate splits by team/season/location
splits as (
    select
        team_id,
        team_name,
        season,
        is_home,
        
        -- Game counts
        count(*) as games,
        
        -- ATS performance
        avg(ats_margin) as ats_margin_avg,
        stddev(ats_margin) as ats_margin_std,
        sum(case when is_cover then 1 else 0 end) as covers,
        avg(case when is_cover then 1.0 else 0.0 end) as cover_rate,
        
        -- O/U performance
        avg(ou_margin) as ou_margin_avg,
        sum(case when is_over then 1 else 0 end) as overs,
        avg(case when is_over then 1.0 else 0.0 end) as over_rate,
        
        -- Straight up
        avg(score_margin) as score_margin_avg,
        sum(case when is_win then 1 else 0 end) as wins,
        avg(case when is_win then 1.0 else 0.0 end) as win_rate,
        
        -- Scoring
        avg(team_points) as avg_points_scored,
        avg(opponent_points) as avg_points_allowed
        
    from base
    group by team_id, team_name, season, is_home
),

-- Pivot to get home and away side by side
pivoted as (
    select
        h.team_id,
        h.team_name,
        h.season,
        
        -- Home stats
        h.games as home_games,
        h.cover_rate as home_cover_rate,
        h.ats_margin_avg as home_ats_margin_avg,
        h.ats_margin_std as home_ats_margin_std,
        h.over_rate as home_over_rate,
        h.win_rate as home_win_rate,
        h.avg_points_scored as home_ppg,
        h.avg_points_allowed as home_papg,
        
        -- Away stats
        a.games as away_games,
        a.cover_rate as away_cover_rate,
        a.ats_margin_avg as away_ats_margin_avg,
        a.ats_margin_std as away_ats_margin_std,
        a.over_rate as away_over_rate,
        a.win_rate as away_win_rate,
        a.avg_points_scored as away_ppg,
        a.avg_points_allowed as away_papg,
        
        -- Differentials (home - away)
        h.cover_rate - a.cover_rate as cover_rate_home_edge,
        h.ats_margin_avg - a.ats_margin_avg as ats_margin_home_edge,
        h.win_rate - a.win_rate as win_rate_home_edge,
        h.avg_points_scored - a.avg_points_scored as ppg_home_edge
        
    from splits h
    join splits a 
        on h.team_id = a.team_id 
        and h.season = a.season
        and h.is_home = true 
        and a.is_home = false
)

select * from pivoted
order by season desc, team_name
