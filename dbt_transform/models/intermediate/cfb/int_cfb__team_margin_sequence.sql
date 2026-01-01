{{
    config(
        materialized='table'
    )
}}

/*
    MARGIN SEQUENCE MODEL (#3)
    
    Grain: 1 row per team per game
    
    Creates arrays of the last N margins for each metric.
    Useful for:
    - Feeding directly to ML models that can handle sequences
    - Analyzing patterns/streaks
    - Custom aggregations
    
    Uses array_agg with ordering to preserve sequence.
*/

with base as (
    select * from {{ ref('int_cfb__game_team_lines') }}
),

-- Get the last N margins as arrays
with_sequences as (
    select
        sport,
        game_id,
        season,
        week,
        game_date,
        team_id,
        team_name,
        opponent_id,
        opponent_name,
        is_home,
        
        -- Current game actuals (for labels)
        ats_margin,
        ou_margin,
        score_margin,
        is_cover,
        is_over,
        
        -- Current game line
        spread_close_for_team,
        total_close,
        
        -- ========== ATS MARGIN SEQUENCES ==========
        -- Last 3 ATS margins (most recent first)
        (
            select array_agg(sub.ats_margin order by sub.game_date desc, sub.game_id desc)
            from {{ ref('int_cfb__game_team_lines') }} sub
            where sub.team_id = base.team_id
              and (sub.game_date < base.game_date 
                   or (sub.game_date = base.game_date and sub.game_id < base.game_id))
            limit 3
        ) as ats_seq_3,
        
        -- Last 5 ATS margins
        (
            select array_agg(sub.ats_margin order by sub.game_date desc, sub.game_id desc)
            from {{ ref('int_cfb__game_team_lines') }} sub
            where sub.team_id = base.team_id
              and (sub.game_date < base.game_date 
                   or (sub.game_date = base.game_date and sub.game_id < base.game_id))
            limit 5
        ) as ats_seq_5,
        
        -- Last 10 ATS margins
        (
            select array_agg(sub.ats_margin order by sub.game_date desc, sub.game_id desc)
            from {{ ref('int_cfb__game_team_lines') }} sub
            where sub.team_id = base.team_id
              and (sub.game_date < base.game_date 
                   or (sub.game_date = base.game_date and sub.game_id < base.game_id))
            limit 10
        ) as ats_seq_10,
        
        -- ========== O/U MARGIN SEQUENCES ==========
        (
            select array_agg(sub.ou_margin order by sub.game_date desc, sub.game_id desc)
            from {{ ref('int_cfb__game_team_lines') }} sub
            where sub.team_id = base.team_id
              and (sub.game_date < base.game_date 
                   or (sub.game_date = base.game_date and sub.game_id < base.game_id))
            limit 10
        ) as ou_seq_10,
        
        -- ========== SCORE MARGIN SEQUENCES ==========
        (
            select array_agg(sub.score_margin order by sub.game_date desc, sub.game_id desc)
            from {{ ref('int_cfb__game_team_lines') }} sub
            where sub.team_id = base.team_id
              and (sub.game_date < base.game_date 
                   or (sub.game_date = base.game_date and sub.game_id < base.game_id))
            limit 10
        ) as score_seq_10
        
    from base
)

select * from with_sequences
