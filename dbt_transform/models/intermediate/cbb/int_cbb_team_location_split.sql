{{
    config(
        materialized='view',
        tags=['intermediate', 'cbb', 'shape']
    )
}}

/*
    LOCATION SPLIT VIEW (vw_team_location_split)

    Purpose: Separate home and away volatility profiles.
    Key insight: Some teams are road warriors (low away variance),
    others collapse on the road (high away variance, poor ATS).

    Calculates rolling stats SEPARATELY for home and away games.
    Uses '1 PRECEDING' to prevent leakage.
*/

with team_games as (
    select * from {{ ref('int_cbb_team_game') }}
),

-- Calculate rolling stats for home games, carried forward to all games
home_stats as (
    select
        game_id,
        team_id,
        game_date,
        is_home,

        -- Rolling stats for HOME games only (using cumulative window on home games)
        -- These values are only populated for home games, will be forward-filled later
        case when is_home then
            avg(cover_margin_team) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as mean_cover_margin_home_last5,

        case when is_home then
            stddev(cover_margin_team) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as stddev_cover_margin_home_last5,

        case when is_home then
            avg(abs(cover_margin_team)) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as mean_abs_cover_margin_home_last5,

        case when is_home then
            avg(case when abs(cover_margin_team) <= 10 then 1.0 else 0.0 end) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as within_10_rate_home_last5,

        case when is_home then
            avg(case when cover_margin_team <= -10 then 1.0 else 0.0 end) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as downside_tail_rate_home_last5,

        case when is_home then
            avg(ats_win_team::numeric) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as ats_win_rate_home_last5,

        case when is_home then
            avg(cover_margin_team) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 10 preceding and 1 preceding
            )
        end as mean_cover_margin_home_last10,

        case when is_home then
            stddev(cover_margin_team) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 10 preceding and 1 preceding
            )
        end as stddev_cover_margin_home_last10,

        case when is_home then
            avg(ats_win_team::numeric) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 10 preceding and 1 preceding
            )
        end as ats_win_rate_home_last10,

        case when is_home then
            avg(total_error) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as mean_total_error_home_last5,

        case when is_home then
            stddev(total_error) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as stddev_total_error_home_last5,

        case when is_home then
            avg(over_win::numeric) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as over_rate_home_last5,

        case when is_home then
            count(*) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 10 preceding and 1 preceding
            )
        end as home_games_in_window_10,

        -- Away stats (only populated for away games)
        case when not is_home then
            avg(cover_margin_team) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as mean_cover_margin_away_last5,

        case when not is_home then
            stddev(cover_margin_team) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as stddev_cover_margin_away_last5,

        case when not is_home then
            avg(abs(cover_margin_team)) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as mean_abs_cover_margin_away_last5,

        case when not is_home then
            avg(case when abs(cover_margin_team) <= 10 then 1.0 else 0.0 end) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as within_10_rate_away_last5,

        case when not is_home then
            avg(case when cover_margin_team <= -10 then 1.0 else 0.0 end) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as downside_tail_rate_away_last5,

        case when not is_home then
            avg(ats_win_team::numeric) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as ats_win_rate_away_last5,

        case when not is_home then
            avg(cover_margin_team) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 10 preceding and 1 preceding
            )
        end as mean_cover_margin_away_last10,

        case when not is_home then
            stddev(cover_margin_team) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 10 preceding and 1 preceding
            )
        end as stddev_cover_margin_away_last10,

        case when not is_home then
            avg(ats_win_team::numeric) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 10 preceding and 1 preceding
            )
        end as ats_win_rate_away_last10,

        case when not is_home then
            avg(total_error) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as mean_total_error_away_last5,

        case when not is_home then
            stddev(total_error) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as stddev_total_error_away_last5,

        case when not is_home then
            avg(over_win::numeric) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 5 preceding and 1 preceding
            )
        end as over_rate_away_last5,

        case when not is_home then
            count(*) over (
                partition by team_id, is_home
                order by game_date, game_id
                rows between 10 preceding and 1 preceding
            )
        end as away_games_in_window_10

    from team_games
),

-- Forward fill: carry forward the last known home/away stats to all games
filled as (
    select
        game_id,
        team_id,
        game_date,
        is_home,

        -- Forward fill home stats (last non-null value)
        last_value(mean_cover_margin_home_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as mean_cover_margin_home_last5,

        last_value(stddev_cover_margin_home_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as stddev_cover_margin_home_last5,

        last_value(mean_abs_cover_margin_home_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as mean_abs_cover_margin_home_last5,

        last_value(within_10_rate_home_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as within_10_rate_home_last5,

        last_value(downside_tail_rate_home_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as downside_tail_rate_home_last5,

        last_value(ats_win_rate_home_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as ats_win_rate_home_last5,

        last_value(mean_cover_margin_home_last10) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as mean_cover_margin_home_last10,

        last_value(stddev_cover_margin_home_last10) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as stddev_cover_margin_home_last10,

        last_value(ats_win_rate_home_last10) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as ats_win_rate_home_last10,

        last_value(mean_total_error_home_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as mean_total_error_home_last5,

        last_value(stddev_total_error_home_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as stddev_total_error_home_last5,

        last_value(over_rate_home_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as over_rate_home_last5,

        last_value(home_games_in_window_10) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as home_games_in_window_10,

        -- Forward fill away stats
        last_value(mean_cover_margin_away_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as mean_cover_margin_away_last5,

        last_value(stddev_cover_margin_away_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as stddev_cover_margin_away_last5,

        last_value(mean_abs_cover_margin_away_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as mean_abs_cover_margin_away_last5,

        last_value(within_10_rate_away_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as within_10_rate_away_last5,

        last_value(downside_tail_rate_away_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as downside_tail_rate_away_last5,

        last_value(ats_win_rate_away_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as ats_win_rate_away_last5,

        last_value(mean_cover_margin_away_last10) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as mean_cover_margin_away_last10,

        last_value(stddev_cover_margin_away_last10) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as stddev_cover_margin_away_last10,

        last_value(ats_win_rate_away_last10) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as ats_win_rate_away_last10,

        last_value(mean_total_error_away_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as mean_total_error_away_last5,

        last_value(stddev_total_error_away_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as stddev_total_error_away_last5,

        last_value(over_rate_away_last5) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as over_rate_away_last5,

        last_value(away_games_in_window_10) over (
            partition by team_id order by game_date, game_id
            rows between unbounded preceding and current row
        ) as away_games_in_window_10

    from home_stats
),

-- Join back to team_games for full context
final as (
    select
        tg.game_id,
        tg.team_id,
        tg.team,
        tg.game_date,
        tg.season,
        tg.team_game_number,
        tg.is_home,

        -- Home performance metrics
        f.mean_cover_margin_home_last5,
        f.stddev_cover_margin_home_last5,
        f.mean_abs_cover_margin_home_last5,
        f.within_10_rate_home_last5,
        f.downside_tail_rate_home_last5,
        f.ats_win_rate_home_last5,
        f.mean_cover_margin_home_last10,
        f.stddev_cover_margin_home_last10,
        f.ats_win_rate_home_last10,
        f.mean_total_error_home_last5,
        f.stddev_total_error_home_last5,
        f.over_rate_home_last5,
        f.home_games_in_window_10,

        -- Away performance metrics
        f.mean_cover_margin_away_last5,
        f.stddev_cover_margin_away_last5,
        f.mean_abs_cover_margin_away_last5,
        f.within_10_rate_away_last5,
        f.downside_tail_rate_away_last5,
        f.ats_win_rate_away_last5,
        f.mean_cover_margin_away_last10,
        f.stddev_cover_margin_away_last10,
        f.ats_win_rate_away_last10,
        f.mean_total_error_away_last5,
        f.stddev_total_error_away_last5,
        f.over_rate_away_last5,
        f.away_games_in_window_10,

        -- HOME/AWAY DIFFERENTIAL METRICS
        coalesce(f.ats_win_rate_home_last5, 0) - coalesce(f.ats_win_rate_away_last5, 0)
            as home_away_ats_differential,

        coalesce(f.mean_cover_margin_home_last5, 0) - coalesce(f.mean_cover_margin_away_last5, 0)
            as home_away_cover_differential,

        coalesce(f.stddev_cover_margin_home_last5, 0) - coalesce(f.stddev_cover_margin_away_last5, 0)
            as home_away_variance_differential,

        -- ROAD WARRIOR / HOME DEPENDENT FLAGS
        case
            when f.ats_win_rate_away_last5 > f.ats_win_rate_home_last5
                 and coalesce(f.stddev_cover_margin_away_last5, 999) < coalesce(f.stddev_cover_margin_home_last5, 0)
            then true else false
        end as is_road_warrior,

        case
            when f.ats_win_rate_home_last5 - coalesce(f.ats_win_rate_away_last5, 0) > 0.20
            then true else false
        end as is_home_dependent,

        case
            when coalesce(f.downside_tail_rate_away_last5, 0) > 0.25
            then true else false
        end as road_collapse_risk

    from team_games tg
    inner join filled f on tg.game_id = f.game_id and tg.team_id = f.team_id
)

select * from final
