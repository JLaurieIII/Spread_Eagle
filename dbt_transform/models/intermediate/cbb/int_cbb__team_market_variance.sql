{{
    config(
        materialized='table'
    )
}}

/*
    ============================================================================
    INTERMEDIATE MODEL: int_cbb__team_market_variance
    ============================================================================

    PURPOSE:
    Quantify how closely each team plays to market expectations for both
    spread and total. This is the core primitive for teaser probability
    calculations — teams with low variance are more predictable against
    the number, making them stronger teaser candidates.

    GRAIN: 1 row per team per season (season-to-date aggregates)

    KEY METRICS:
    - spread_error = actual_margin - market_spread (from team's POV)
    - total_error  = actual_total  - market_total
    - MAD, RMS, mean error for each
    - Bayesian shrinkage for small samples (toward league average)
    - Z-scores, percentiles, and variance buckets for normalization

    COMPLEMENTS: int_cbb__team_spread_volatility (game-level rolling windows)
    UNLOCKS:     Game-level sigma estimation for teaser probability (Phi model)

    ============================================================================
*/

with game_errors as (
    -- Per-team per-game error calculation (unpivot home/away)
    select
        bl.game_id,
        bl.start_date::date as game_date,
        bl.season,
        bl.home_team_id as team_id,
        bl.home_team as team_name,
        -- Spread error: actual margin minus market spread (home POV)
        (bl.home_score - bl.away_score) - bl.spread as spread_error,
        -- Total error: actual total minus market total
        (bl.home_score + bl.away_score) - bl.over_under as total_error
    from cbb.betting_lines bl
    where bl.provider = 'Bovada'
      and bl.home_score is not null
      and bl.home_score > 0
      and bl.away_score is not null
      and bl.away_score > 0
      and bl.spread is not null
      and bl.over_under is not null

    union all

    select
        bl.game_id,
        bl.start_date::date as game_date,
        bl.season,
        bl.away_team_id as team_id,
        bl.away_team as team_name,
        -- Spread error: actual margin minus market spread (away POV — flip sign)
        (bl.away_score - bl.home_score) - (-bl.spread) as spread_error,
        -- Total error: same regardless of perspective
        (bl.home_score + bl.away_score) - bl.over_under as total_error
    from cbb.betting_lines bl
    where bl.provider = 'Bovada'
      and bl.home_score is not null
      and bl.home_score > 0
      and bl.away_score is not null
      and bl.away_score > 0
      and bl.spread is not null
      and bl.over_under is not null
),

season_aggregates as (
    -- Season-to-date variance metrics per team
    select
        team_id,
        team_name,
        season,
        count(*) as games_played,

        -- Spread variance metrics
        avg(abs(spread_error)) as spread_mad,
        sqrt(avg(spread_error * spread_error)) as spread_rms,
        avg(spread_error) as spread_mean_error,

        -- Total variance metrics
        avg(abs(total_error)) as total_mad,
        sqrt(avg(total_error * total_error)) as total_rms,
        avg(total_error) as total_mean_error

    from game_errors
    group by team_id, team_name, season
),

global_averages as (
    -- League-wide averages for shrinkage (only teams with sufficient sample)
    select
        season,
        avg(spread_mad) as global_spread_mad,
        avg(spread_rms) as global_spread_rms,
        avg(total_mad) as global_total_mad,
        avg(total_rms) as global_total_rms
    from season_aggregates
    where games_played >= 10
    group by season
),

stabilized as (
    -- Apply Bayesian shrinkage for small samples
    -- Weight ramps linearly from 0 (0 games) to 1 (15+ games)
    select
        sa.team_id,
        sa.team_name,
        sa.season,
        sa.games_played,

        -- Raw metrics
        sa.spread_mad,
        sa.spread_rms,
        sa.spread_mean_error,
        sa.total_mad,
        sa.total_rms,
        sa.total_mean_error,

        -- Shrinkage weight
        least(sa.games_played, 15.0) / 15.0 as shrinkage_weight,

        -- Stabilized spread metrics
        (least(sa.games_played, 15.0) / 15.0) * sa.spread_mad
            + (1.0 - least(sa.games_played, 15.0) / 15.0) * ga.global_spread_mad
            as spread_mad_stabilized,
        (least(sa.games_played, 15.0) / 15.0) * sa.spread_rms
            + (1.0 - least(sa.games_played, 15.0) / 15.0) * ga.global_spread_rms
            as spread_rms_stabilized,

        -- Stabilized total metrics
        (least(sa.games_played, 15.0) / 15.0) * sa.total_mad
            + (1.0 - least(sa.games_played, 15.0) / 15.0) * ga.global_total_mad
            as total_mad_stabilized,
        (least(sa.games_played, 15.0) / 15.0) * sa.total_rms
            + (1.0 - least(sa.games_played, 15.0) / 15.0) * ga.global_total_rms
            as total_rms_stabilized

    from season_aggregates sa
    inner join global_averages ga
        on sa.season = ga.season
    where sa.games_played >= 8
),

normalized as (
    -- Z-scores, percentiles, and variance buckets
    select
        team_id,
        team_name,
        season,
        games_played,

        -- Raw metrics
        spread_mad,
        spread_rms,
        spread_mean_error,
        total_mad,
        total_rms,
        total_mean_error,

        -- Stabilized metrics
        spread_rms_stabilized,
        total_rms_stabilized,

        -- Z-scores (using stabilized RMS)
        case
            when stddev(spread_rms_stabilized) over (partition by season) > 0
            then (spread_rms_stabilized - avg(spread_rms_stabilized) over (partition by season))
                 / stddev(spread_rms_stabilized) over (partition by season)
            else 0
        end as spread_rms_z,

        case
            when stddev(total_rms_stabilized) over (partition by season) > 0
            then (total_rms_stabilized - avg(total_rms_stabilized) over (partition by season))
                 / stddev(total_rms_stabilized) over (partition by season)
            else 0
        end as total_rms_z,

        -- Percentile ranks (0 = tightest variance, 1 = wildest)
        percent_rank() over (partition by season order by spread_rms_stabilized) as spread_rms_percentile,
        percent_rank() over (partition by season order by total_rms_stabilized) as total_rms_percentile,

        -- Variance buckets (1 = tightest, 5 = wildest)
        ntile(5) over (partition by season order by spread_rms_stabilized) as spread_variance_bucket,
        ntile(5) over (partition by season order by total_rms_stabilized) as total_variance_bucket

    from stabilized
)

select
    team_id,
    team_name,
    season,
    games_played,

    -- Raw spread metrics
    round(spread_mad::numeric, 2) as spread_mad,
    round(spread_rms::numeric, 2) as spread_rms,
    round(spread_mean_error::numeric, 2) as spread_mean_error,

    -- Raw total metrics
    round(total_mad::numeric, 2) as total_mad,
    round(total_rms::numeric, 2) as total_rms,
    round(total_mean_error::numeric, 2) as total_mean_error,

    -- Stabilized (shrinkage-adjusted)
    round(spread_rms_stabilized::numeric, 2) as spread_rms_stabilized,
    round(total_rms_stabilized::numeric, 2) as total_rms_stabilized,

    -- Normalized
    round(spread_rms_z::numeric, 3) as spread_rms_z,
    round(total_rms_z::numeric, 3) as total_rms_z,
    round(spread_rms_percentile::numeric, 3) as spread_rms_percentile,
    round(total_rms_percentile::numeric, 3) as total_rms_percentile,
    spread_variance_bucket,
    total_variance_bucket

from normalized
order by season desc, total_rms_stabilized asc
