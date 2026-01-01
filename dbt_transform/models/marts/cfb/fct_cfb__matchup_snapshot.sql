{{
    config(
        materialized='table'
    )
}}

/*
    MATCHUP SNAPSHOT MODEL (#4)
    
    Grain: 1 row per team per game
    
    THE ML-READY TABLE: Combines team's rolling stats with opponent's rolling stats
    at the time of each game. This is what you feed to your model.
    
    Structure:
    - Game identifiers
    - Team rolling features (prefixed with team_)
    - Opponent rolling features (prefixed with opp_)
    - Delta features (team - opponent)
    - Labels (actual outcome)
*/

with team_form as (
    select * from {{ ref('int_cfb__team_rolling_form') }}
),

-- Self-join to get opponent's rolling stats at time of game
matchup as (
    select
        -- === GAME IDENTIFIERS ===
        t.sport,
        t.game_id,
        t.season,
        t.week,
        t.game_date,
        t.is_neutral_site,
        t.is_conference_game,
        
        -- === TEAM INFO ===
        t.team_id,
        t.team_name,
        t.opponent_id,
        t.opponent_name,
        t.is_home,
        
        -- === LINE INFO ===
        t.spread_close_for_team,
        t.total_close,
        
        -- === TEAM ROLLING FEATURES ===
        t.team_game_num,
        t.ats_margin_last5_avg as team_ats_l5_avg,
        t.ats_margin_last5_std as team_ats_l5_std,
        t.ats_margin_last10_avg as team_ats_l10_avg,
        t.ats_margin_last10_std as team_ats_l10_std,
        t.cover_rate_last5 as team_cover_l5,
        t.cover_rate_last10 as team_cover_l10,
        t.ou_margin_last5_avg as team_ou_l5_avg,
        t.ou_margin_last10_avg as team_ou_l10_avg,
        t.over_rate_last10 as team_over_l10,
        t.score_margin_last5_avg as team_margin_l5_avg,
        t.score_margin_last10_avg as team_margin_l10_avg,
        t.win_rate_last5 as team_win_l5,
        t.win_rate_last10 as team_win_l10,
        
        -- === OPPONENT ROLLING FEATURES ===
        o.team_game_num as opp_game_num,
        o.ats_margin_last5_avg as opp_ats_l5_avg,
        o.ats_margin_last5_std as opp_ats_l5_std,
        o.ats_margin_last10_avg as opp_ats_l10_avg,
        o.ats_margin_last10_std as opp_ats_l10_std,
        o.cover_rate_last5 as opp_cover_l5,
        o.cover_rate_last10 as opp_cover_l10,
        o.ou_margin_last5_avg as opp_ou_l5_avg,
        o.ou_margin_last10_avg as opp_ou_l10_avg,
        o.over_rate_last10 as opp_over_l10,
        o.score_margin_last5_avg as opp_margin_l5_avg,
        o.score_margin_last10_avg as opp_margin_l10_avg,
        o.win_rate_last5 as opp_win_l5,
        o.win_rate_last10 as opp_win_l10,
        
        -- === DELTA FEATURES (team - opponent) ===
        t.ats_margin_last5_avg - o.ats_margin_last5_avg as delta_ats_l5,
        t.ats_margin_last10_avg - o.ats_margin_last10_avg as delta_ats_l10,
        t.cover_rate_last10 - o.cover_rate_last10 as delta_cover_l10,
        t.score_margin_last10_avg - o.score_margin_last10_avg as delta_margin_l10,
        t.win_rate_last10 - o.win_rate_last10 as delta_win_l10,
        
        -- === LABELS (actual outcomes) ===
        t.team_points,
        t.opponent_points,
        t.score_margin,
        t.ats_margin,
        t.ou_margin,
        t.is_cover,
        t.is_over,
        t.is_win
        
    from team_form t
    -- Join opponent's stats from their perspective in the SAME game
    left join team_form o 
        on t.game_id = o.game_id 
        and t.opponent_id = o.team_id
)

select * from matchup
-- Filter to games where both teams have sufficient history
where team_game_num >= 3 
  and opp_game_num >= 3
order by game_date, game_id, is_home desc
