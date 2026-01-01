{{
    config(
        materialized='table'
    )
}}

/*
    ROLLING FORM MODEL (#2)
    
    Grain: 1 row per team per game (same as foundation)
    
    Adds rolling statistics "as of that game" - using only PRIOR games.
    This is critical for ML: no future leakage.
    
    Window: ROWS BETWEEN N PRECEDING AND 1 PRECEDING
    (excludes current game, only looks at past)
*/

with base as (
    select * from {{ ref('int_cfb__game_team_lines') }}
),

with_rolling as (
    select
        *,
        
        -- Game sequence number for this team (for filtering early-season games)
        row_number() over (
            partition by team_id, season 
            order by game_date, game_id
        ) as team_game_num,
        
        -- ========== ATS MARGIN ROLLING ==========
        -- Last 3 games
        avg(ats_margin) over (
            partition by team_id 
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as ats_margin_last3_avg,
        
        stddev(ats_margin) over (
            partition by team_id 
            order by game_date, game_id
            rows between 3 preceding and 1 preceding
        ) as ats_margin_last3_std,
        
        -- Last 5 games
        avg(ats_margin) over (
            partition by team_id 
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as ats_margin_last5_avg,
        
        stddev(ats_margin) over (
            partition by team_id 
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as ats_margin_last5_std,
        
        -- Last 10 games
        avg(ats_margin) over (
            partition by team_id 
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as ats_margin_last10_avg,
        
        stddev(ats_margin) over (
            partition by team_id 
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as ats_margin_last10_std,
        
        min(ats_margin) over (
            partition by team_id 
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as ats_margin_last10_min,
        
        max(ats_margin) over (
            partition by team_id 
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as ats_margin_last10_max,
        
        -- ========== COVER RATE ROLLING ==========
        avg(case when is_cover then 1.0 else 0.0 end) over (
            partition by team_id 
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as cover_rate_last5,
        
        avg(case when is_cover then 1.0 else 0.0 end) over (
            partition by team_id 
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as cover_rate_last10,
        
        avg(case when is_cover then 1.0 else 0.0 end) over (
            partition by team_id 
            order by game_date, game_id
            rows between 20 preceding and 1 preceding
        ) as cover_rate_last20,
        
        -- ========== O/U MARGIN ROLLING ==========
        avg(ou_margin) over (
            partition by team_id 
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as ou_margin_last5_avg,
        
        stddev(ou_margin) over (
            partition by team_id 
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as ou_margin_last5_std,
        
        avg(ou_margin) over (
            partition by team_id 
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as ou_margin_last10_avg,
        
        -- ========== OVER RATE ROLLING ==========
        avg(case when is_over then 1.0 else 0.0 end) over (
            partition by team_id 
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as over_rate_last10,
        
        -- ========== SCORE MARGIN ROLLING ==========
        avg(score_margin) over (
            partition by team_id 
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as score_margin_last5_avg,
        
        stddev(score_margin) over (
            partition by team_id 
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as score_margin_last5_std,
        
        avg(score_margin) over (
            partition by team_id 
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as score_margin_last10_avg,
        
        -- ========== WIN RATE ROLLING ==========
        avg(case when is_win then 1.0 else 0.0 end) over (
            partition by team_id 
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ) as win_rate_last5,
        
        avg(case when is_win then 1.0 else 0.0 end) over (
            partition by team_id 
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        ) as win_rate_last10
        
    from base
)

select * from with_rolling
