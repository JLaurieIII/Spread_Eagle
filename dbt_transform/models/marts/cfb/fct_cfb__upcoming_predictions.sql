{{
    config(
        materialized='table'
    )
}}

/*
    UPCOMING GAMES PREDICTIONS MODEL

    Grain: 1 row per team per upcoming game

    Joins upcoming games with each team's historical rolling features.
    This is what the ML model uses to predict games that haven't happened yet.

    Key difference from matchup_snapshot:
    - No actual scores (game hasn't happened)
    - Uses most recent rolling stats from completed games
*/

with games as (
    select * from {{ ref('stg_cfb__games') }}
    where is_completed = false  -- Only upcoming games
),

lines as (
    -- Aggregate across providers for stable pre-game lines
    select
        game_id,
        avg(spread_close) as spread_close,
        avg(spread_open) as spread_open,
        avg(total_close) as total_close,
        avg(total_open) as total_open
    from {{ ref('stg_cfb__betting_lines') }}
    where spread_close is not null
    group by game_id
),

-- Get the most recent rolling stats for each team
-- Using completed games only for the rolling calcs
team_latest_form as (
    select distinct on (team_id)
        team_id,
        team_name,
        ats_margin_last5_avg,
        ats_margin_last10_avg,
        ats_margin_last5_std,
        ats_margin_last10_std,
        cover_rate_last5,
        cover_rate_last10,
        ou_margin_last5_avg,
        ou_margin_last10_avg,
        over_rate_last10,
        score_margin_last5_avg,
        score_margin_last10_avg,
        win_rate_last5,
        win_rate_last10
    from {{ ref('int_cfb__team_rolling_form') }}
    order by team_id, game_date desc, game_id desc
),

-- Build upcoming matchups
upcoming_home as (
    select
        'cfb' as sport,
        g.game_id,
        g.season,
        g.week,
        g.game_date,
        g.is_neutral_site,
        g.is_conference_game,

        g.home_id as team_id,
        g.home_team as team_name,
        g.away_id as opponent_id,
        g.away_team as opponent_name,
        true as is_home,

        l.spread_close as spread_close_for_team,
        l.total_close,

        -- Team rolling features
        t.ats_margin_last5_avg as team_ats_l5_avg,
        t.ats_margin_last10_avg as team_ats_l10_avg,
        t.ats_margin_last5_std as team_ats_l5_std,
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

        -- Opponent rolling features
        o.ats_margin_last5_avg as opp_ats_l5_avg,
        o.ats_margin_last10_avg as opp_ats_l10_avg,
        o.ats_margin_last5_std as opp_ats_l5_std,
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

        -- Delta features
        t.ats_margin_last5_avg - o.ats_margin_last5_avg as delta_ats_l5,
        t.ats_margin_last10_avg - o.ats_margin_last10_avg as delta_ats_l10,
        t.cover_rate_last10 - o.cover_rate_last10 as delta_cover_l10,
        t.score_margin_last10_avg - o.score_margin_last10_avg as delta_margin_l10

    from games g
    left join lines l on g.game_id = l.game_id
    left join team_latest_form t on g.home_id = t.team_id
    left join team_latest_form o on g.away_id = o.team_id
    where l.spread_close is not null
),

upcoming_away as (
    select
        'cfb' as sport,
        g.game_id,
        g.season,
        g.week,
        g.game_date,
        g.is_neutral_site,
        g.is_conference_game,

        g.away_id as team_id,
        g.away_team as team_name,
        g.home_id as opponent_id,
        g.home_team as opponent_name,
        false as is_home,

        -1 * l.spread_close as spread_close_for_team,
        l.total_close,

        -- Team rolling features (away team)
        t.ats_margin_last5_avg as team_ats_l5_avg,
        t.ats_margin_last10_avg as team_ats_l10_avg,
        t.ats_margin_last5_std as team_ats_l5_std,
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

        -- Opponent rolling features (home team)
        o.ats_margin_last5_avg as opp_ats_l5_avg,
        o.ats_margin_last10_avg as opp_ats_l10_avg,
        o.ats_margin_last5_std as opp_ats_l5_std,
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

        -- Delta features
        t.ats_margin_last5_avg - o.ats_margin_last5_avg as delta_ats_l5,
        t.ats_margin_last10_avg - o.ats_margin_last10_avg as delta_ats_l10,
        t.cover_rate_last10 - o.cover_rate_last10 as delta_cover_l10,
        t.score_margin_last10_avg - o.score_margin_last10_avg as delta_margin_l10

    from games g
    left join lines l on g.game_id = l.game_id
    left join team_latest_form t on g.away_id = t.team_id
    left join team_latest_form o on g.home_id = o.team_id
    where l.spread_close is not null
)

select * from upcoming_home
union all
select * from upcoming_away
order by game_date, game_id, is_home desc
