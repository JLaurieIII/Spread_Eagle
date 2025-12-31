{{
    config(
        materialized='view',
        tags=['intermediate', 'cbb']
    )
}}

/*
    CANONICAL ERROR SPACE MODEL

    This model defines reality vs Vegas:
    - Vegas sets the CENTER (spread/total)
    - We measure how far reality landed from that center

    Key derived fields:
    - margin_home: actual home margin (home_score - away_score)
    - spread_error_home: how far from implied spread (positive = home beat expectations)
    - cover_margin_home: points by which home covered (positive = home covered)
    - total_error: how far total landed from O/U (positive = over)
*/

with games as (
    select * from {{ ref('stg_cbb_games') }}
    where is_completed = true
),

lines as (
    select * from {{ ref('stg_cbb_betting_lines') }}
),

joined as (
    select
        -- Keys
        g.game_id,
        g.game_date,
        g.game_date_local,
        g.season,
        g.season_type,

        -- Teams
        g.home_team_id,
        g.home_team,
        g.home_conference,
        g.away_team_id,
        g.away_team,
        g.away_conference,

        -- Game context
        g.neutral_site,
        g.conference_game,
        g.tournament,

        -- Final scores
        g.home_score,
        g.away_score,

        -- Lines
        l.closing_spread_home,
        l.opening_spread_home,
        l.closing_total,
        l.opening_total,
        l.spread_movement,
        l.total_movement,
        l.home_moneyline,
        l.away_moneyline,
        l.provider,

        -- ===========================================
        -- CORE DERIVED METRICS (THE ERROR SPACE)
        -- ===========================================

        -- Actual margin (home perspective)
        g.home_score - g.away_score as margin_home,

        -- Total points scored
        g.home_score + g.away_score as total_points,

        -- Implied home margin from spread
        -- If spread is -5 (home favored by 5), implied margin = 5
        -l.closing_spread_home as implied_margin_home,

        -- Spread error: how far home team beat/missed expectations
        -- Positive = home exceeded expectations
        (g.home_score - g.away_score) - (-l.closing_spread_home) as spread_error_home,

        -- Cover margin: points by which home covered the spread
        -- cover_margin = margin + spread (since spread is negative for home fav)
        -- If home -5 and wins by 10: cover_margin = 10 + (-5) = 5 (covered by 5)
        -- If home -5 and wins by 3: cover_margin = 3 + (-5) = -2 (failed to cover by 2)
        (g.home_score - g.away_score) + l.closing_spread_home as cover_margin_home,

        -- Total error: how far over/under the total
        -- Positive = game went over
        (g.home_score + g.away_score) - l.closing_total as total_error,

        -- ===========================================
        -- ATS WIN FLAGS (NULL on push for clean stats)
        -- ===========================================

        case
            when (g.home_score - g.away_score) + l.closing_spread_home > 0 then 1
            when (g.home_score - g.away_score) + l.closing_spread_home < 0 then 0
            else null  -- push
        end as ats_win_home,

        case
            when (g.home_score - g.away_score) + l.closing_spread_home = 0 then true
            else false
        end as ats_push_flag,

        -- ===========================================
        -- OVER/UNDER FLAGS
        -- ===========================================

        case
            when (g.home_score + g.away_score) - l.closing_total > 0 then 1
            when (g.home_score + g.away_score) - l.closing_total < 0 then 0
            else null  -- push
        end as over_win,

        case
            when (g.home_score + g.away_score) - l.closing_total = 0 then true
            else false
        end as total_push_flag,

        -- ===========================================
        -- ABSOLUTE DEVIATIONS (FOR VOLATILITY)
        -- ===========================================

        abs((g.home_score - g.away_score) + l.closing_spread_home) as abs_cover_margin,
        abs((g.home_score + g.away_score) - l.closing_total) as abs_total_error

    from games g
    inner join lines l on g.game_id = l.game_id
    where
        -- Must have valid lines and scores
        l.closing_spread_home is not null
        and g.home_score is not null
        and g.away_score is not null
)

select * from joined
