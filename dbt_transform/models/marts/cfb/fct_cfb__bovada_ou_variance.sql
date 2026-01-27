{{
    config(
        materialized='view'
    )
}}

/*
    Bovada over/under variance and context by team-game
    
    Grain: 1 row per team per game (home + away)
    Filters: Bovada totals only
    
    Metrics:
    - Signed OU margin vs Bovada closing total (positive = over)
    - Rolling variance of OU margin (prev 3 and prev 5 games)
    - Season-to-date variance of OU margin
    - Season average total points
    - Season arrays of total points and OU margins (ordered)
*/

with games as (
    select
        game_id,
        season,
        week,
        season_type,
        game_date,
        is_neutral_site,
        is_conference_game,
        home_id,
        home_team,
        home_points,
        away_id,
        away_team,
        away_points
    from {{ ref('stg_cfb__games') }}
    where home_points is not null
      and away_points is not null
),

bovada_lines as (
    select
        game_id,
        total_open,
        total_close
    from {{ ref('stg_cfb__betting_lines') }}
    where provider = 'Bovada'
      and total_close is not null
),

team_games as (
    -- Home team perspective
    select
        'cfb' as sport,
        g.game_id,
        g.season,
        g.week,
        g.season_type,
        g.game_date,
        g.is_neutral_site,
        g.is_conference_game,
        g.home_id as team_id,
        g.home_team as team_name,
        g.away_id as opponent_id,
        g.away_team as opponent_name,
        true as is_home,
        g.home_points as team_points,
        g.away_points as opponent_points,
        b.total_open as bovada_total_open,
        b.total_close as bovada_total_close
    from games g
    left join bovada_lines b on g.game_id = b.game_id

    union all

    -- Away team perspective
    select
        'cfb' as sport,
        g.game_id,
        g.season,
        g.week,
        g.season_type,
        g.game_date,
        g.is_neutral_site,
        g.is_conference_game,
        g.away_id as team_id,
        g.away_team as team_name,
        g.home_id as opponent_id,
        g.home_team as opponent_name,
        false as is_home,
        g.away_points as team_points,
        g.home_points as opponent_points,
        b.total_open as bovada_total_open,
        b.total_close as bovada_total_close
    from games g
    left join bovada_lines b on g.game_id = b.game_id
),

with_margins as (
    select
        *,
        team_points + opponent_points as total_points,
        (team_points + opponent_points) - bovada_total_close as ou_margin_close,
        (team_points + opponent_points) - bovada_total_open as ou_margin_open,
        case
            when (team_points + opponent_points) - bovada_total_close > 0 then true
            when (team_points + opponent_points) - bovada_total_close < 0 then false
            else null
        end as is_over_close,
        case when (team_points + opponent_points) - bovada_total_close = 0 then true else false end as is_push_close
    from team_games
    where bovada_total_close is not null
),

with_windows as (
    select
        sport,
        game_id,
        season,
        week,
        season_type,
        game_date,
        is_neutral_site,
        is_conference_game,
        team_id,
        team_name,
        opponent_id,
        opponent_name,
        is_home,
        team_points,
        opponent_points,
        bovada_total_open,
        bovada_total_close,
        total_points,
        ou_margin_close,
        ou_margin_open,
        is_over_close,
        is_push_close,

        -- Rolling variance (exclude current game)
        var_samp(ou_margin_close::double precision) over prev_3 as ou_margin_var_prev_3,
        var_samp(ou_margin_close::double precision) over prev_5 as ou_margin_var_prev_5,

        -- Season-to-date variance (includes current game)
        var_samp(ou_margin_close::double precision) over season_win as ou_margin_var_season,

        -- Season aggregates
        avg(total_points) over season_win as avg_total_points_season,
        array_agg(total_points) over season_win as season_total_points_list,
        array_agg(ou_margin_close) over season_win as season_ou_margin_list
    from with_margins
    window
        team_win as (partition by team_id order by game_date, game_id),
        prev_3 as (partition by team_id order by game_date, game_id rows between 3 preceding and 1 preceding),
        prev_5 as (partition by team_id order by game_date, game_id rows between 5 preceding and 1 preceding),
        season_win as (partition by team_id, season order by game_date, game_id)
)

select * 
from with_windows
order by game_date, game_id, is_home desc
