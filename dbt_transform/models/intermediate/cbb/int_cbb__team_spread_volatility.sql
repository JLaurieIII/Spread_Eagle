{{
    config(
        materialized='table'
    )
}}

/*
    ============================================================================
    INTERMEDIATE MODEL: int_cbb__team_spread_volatility
    ============================================================================

    PURPOSE:
    Calculate rolling volatility metrics for each team's spread coverage behavior.
    These metrics identify "predictable" teams for teaser betting strategies.

    KEY INSIGHT:
    For teaser betting (+8 or +10 points), we want teams that:
    1. Consistently play close to the spread (low stddev in cover margin)
    2. Rarely get blown out (low tail risk)
    3. Have high historical teaser survival rates

    GRAIN: 1 row per game per team
    - Rolling windows: L5, L10 (last 5, 10 games)
    - All metrics EXCLUDE current game (no data leakage)
    - Partitioned by team + season

    METRICS:
    - Cover margin = (team_score - opponent_score) + spread_faced
      - Positive = covered, Negative = failed to cover
    - Teaser survival = would +8 or +10 points have resulted in a win?

    ============================================================================
*/

with game_spreads as (
    -- Get spread outcomes for each team's games
    select
        bl.game_id,
        bl.start_date::date as game_date,
        bl.season,
        -- Team perspective (home)
        bl.home_team_id as team_id,
        bl.home_team as team_name,
        bl.home_score as team_score,
        bl.away_score as opponent_score,
        bl.spread as spread_faced,  -- negative = favored
        true as is_home,
        -- Calculated fields
        (bl.home_score - bl.away_score) as point_margin,
        (bl.home_score - bl.away_score) + bl.spread as cover_margin
    from cbb.betting_lines bl
    where bl.provider = 'Bovada'
      and bl.home_score is not null
      and bl.home_score > 0
      and bl.spread is not null

    union all

    select
        bl.game_id,
        bl.start_date::date as game_date,
        bl.season,
        -- Team perspective (away)
        bl.away_team_id as team_id,
        bl.away_team as team_name,
        bl.away_score as team_score,
        bl.home_score as opponent_score,
        -bl.spread as spread_faced,  -- flip for away team
        false as is_home,
        -- Calculated fields
        (bl.away_score - bl.home_score) as point_margin,
        (bl.away_score - bl.home_score) + (-bl.spread) as cover_margin
    from cbb.betting_lines bl
    where bl.provider = 'Bovada'
      and bl.away_score is not null
      and bl.away_score > 0
      and bl.spread is not null
),

ordered_games as (
    select
        *,
        -- Teaser outcomes (did +8 or +10 pts result in covering?)
        case when cover_margin >= -8 then 1 else 0 end as teaser_8_win,
        case when cover_margin >= -10 then 1 else 0 end as teaser_10_win,
        -- Close game indicators (exclusive: < not <= because exactly at boundary = loss)
        case when abs(cover_margin) < 5 then 1 else 0 end as within_5,
        case when abs(cover_margin) < 6 then 1 else 0 end as within_6,
        case when abs(cover_margin) < 7 then 1 else 0 end as within_7,
        case when abs(cover_margin) < 8 then 1 else 0 end as within_8,
        case when abs(cover_margin) < 10 then 1 else 0 end as within_10,
        -- Blowout loss indicator (lost by 15+ after spread)
        case when cover_margin <= -15 then 1 else 0 end as blowout_loss,
        -- Game number within season
        row_number() over (
            partition by team_id, season
            order by game_date, game_id
        ) as season_game_num
    from game_spreads
),

rolling_volatility as (
    select
        game_id,
        game_date,
        season,
        team_id,
        team_name,
        is_home,
        spread_faced,
        point_margin,
        cover_margin,
        teaser_8_win,
        teaser_10_win,
        -- Raw within_X flags for this game (for testing/debugging)
        within_5,
        within_6,
        within_7,
        within_8,
        within_10,
        blowout_loss,
        season_game_num,

        -- Games played (excluding current)
        season_game_num - 1 as games_played,

        -- =======================================================================
        -- COVER MARGIN VOLATILITY (lower = more predictable)
        -- =======================================================================
        avg(cover_margin) over w_prev_5 as avg_cover_margin_l5,
        avg(cover_margin) over w_prev_10 as avg_cover_margin_l10,
        stddev_samp(cover_margin) over w_prev_5 as stddev_cover_margin_l5,
        stddev_samp(cover_margin) over w_prev_10 as stddev_cover_margin_l10,

        -- =======================================================================
        -- CLOSE GAME RATES (higher = more predictable)
        -- =======================================================================
        avg(within_5::float) over w_prev_10 as within_5_rate_l10,
        avg(within_6::float) over w_prev_10 as within_6_rate_l10,
        avg(within_7::float) over w_prev_10 as within_7_rate_l10,
        avg(within_8::float) over w_prev_10 as within_8_rate_l10,
        avg(within_10::float) over w_prev_10 as within_10_rate_l10,

        -- =======================================================================
        -- TEASER SURVIVAL RATES (higher = better for teasers)
        -- =======================================================================
        avg(teaser_8_win::float) over w_prev_5 as teaser_8_survival_l5,
        avg(teaser_8_win::float) over w_prev_10 as teaser_8_survival_l10,
        avg(teaser_10_win::float) over w_prev_5 as teaser_10_survival_l5,
        avg(teaser_10_win::float) over w_prev_10 as teaser_10_survival_l10,

        -- =======================================================================
        -- TAIL RISK METRICS (lower = safer)
        -- =======================================================================
        avg(blowout_loss::float) over w_prev_10 as blowout_rate_l10,
        min(cover_margin) over w_prev_10 as worst_cover_l10,

        -- =======================================================================
        -- ATS RECORD (context)
        -- =======================================================================
        avg(case when cover_margin > 0 then 1.0 else 0.0 end) over w_prev_5 as ats_win_rate_l5,
        avg(case when cover_margin > 0 then 1.0 else 0.0 end) over w_prev_10 as ats_win_rate_l10

    from ordered_games

    window
        w_prev_5 as (
            partition by team_id, season
            order by game_date, game_id
            rows between 5 preceding and 1 preceding
        ),
        w_prev_10 as (
            partition by team_id, season
            order by game_date, game_id
            rows between 10 preceding and 1 preceding
        )
)

select * from rolling_volatility
order by game_date desc, game_id, team_id
