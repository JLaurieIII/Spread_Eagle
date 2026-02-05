{{
    config(
        materialized='table',
        schema='intermediate_cbb'
    )
}}

/*
    TEAM DISTRIBUTION STATS
    =======================
    Aggregates historical margin distributions for KDE visualization.

    For each team/season, provides:
    - All individual margins (for frontend KDE calculation)
    - Percentiles (p5, p25, p50, p75, p95)
    - Distribution shape metrics (skewness approximation)
    - Bucketed histogram data

    Used by: Frontend KDE graphs, API distribution endpoint
*/

with spread_margins as (
    select
        team_id,
        team_name,
        season,
        game_date,
        cover_margin,
        -- Flags for bucketing
        case
            when abs(cover_margin) < 5 then 'within_5'
            when abs(cover_margin) < 6 then 'within_6'
            when abs(cover_margin) < 8 then 'within_8'
            when abs(cover_margin) < 10 then 'within_10'
            when abs(cover_margin) < 15 then 'within_15'
            else 'beyond_15'
        end as spread_bucket
    from {{ ref('int_cbb__team_spread_volatility') }}
    where cover_margin is not null
),

total_margins as (
    select
        team_id,
        team_name,
        season,
        game_date,
        total_margin,
        -- Flags for bucketing
        case
            when abs(total_margin) < 5 then 'within_5'
            when abs(total_margin) < 6 then 'within_6'
            when abs(total_margin) < 8 then 'within_8'
            when abs(total_margin) < 10 then 'within_10'
            when abs(total_margin) < 15 then 'within_15'
            else 'beyond_15'
        end as total_bucket
    from {{ ref('int_cbb__team_ou_trends') }}
    where total_margin is not null
),

-- Aggregate spread distribution per team/season
spread_distribution as (
    select
        team_id,
        team_name,
        season,

        -- Sample size
        count(*) as spread_games,

        -- Central tendency
        avg(cover_margin) as spread_mean,
        percentile_cont(0.5) within group (order by cover_margin) as spread_median,

        -- Dispersion
        stddev(cover_margin) as spread_std,
        percentile_cont(0.75) within group (order by cover_margin)
            - percentile_cont(0.25) within group (order by cover_margin) as spread_iqr,

        -- Percentiles for box plot / distribution shape
        percentile_cont(0.05) within group (order by cover_margin) as spread_p5,
        percentile_cont(0.25) within group (order by cover_margin) as spread_p25,
        percentile_cont(0.75) within group (order by cover_margin) as spread_p75,
        percentile_cont(0.95) within group (order by cover_margin) as spread_p95,

        -- Extremes
        min(cover_margin) as spread_min,
        max(cover_margin) as spread_max,

        -- Bucket counts (for histogram)
        sum(case when spread_bucket = 'within_5' then 1 else 0 end) as spread_within_5_count,
        sum(case when spread_bucket = 'within_6' then 1 else 0 end) as spread_within_6_count,
        sum(case when spread_bucket = 'within_8' then 1 else 0 end) as spread_within_8_count,
        sum(case when spread_bucket = 'within_10' then 1 else 0 end) as spread_within_10_count,
        sum(case when spread_bucket = 'within_15' then 1 else 0 end) as spread_within_15_count,
        sum(case when spread_bucket = 'beyond_15' then 1 else 0 end) as spread_beyond_15_count,

        -- Rates (exclusive: < not <=)
        avg(case when abs(cover_margin) < 6 then 1.0 else 0.0 end) as spread_within_6_rate,
        avg(case when abs(cover_margin) < 8 then 1.0 else 0.0 end) as spread_within_8_rate,
        avg(case when abs(cover_margin) < 10 then 1.0 else 0.0 end) as spread_within_10_rate,

        -- Skewness approximation (Pearson's second coefficient)
        -- Skew = 3 * (mean - median) / stddev
        case
            when stddev(cover_margin) > 0 then
                3.0 * (avg(cover_margin) - percentile_cont(0.5) within group (order by cover_margin))
                / nullif(stddev(cover_margin), 0)
            else 0
        end as spread_skewness,

        -- All margins as JSON array (for frontend KDE)
        json_agg(cover_margin order by game_date) as spread_margins_json

    from spread_margins
    group by team_id, team_name, season
),

-- Aggregate total distribution per team/season
total_distribution as (
    select
        team_id,
        team_name,
        season,

        -- Sample size
        count(*) as total_games,

        -- Central tendency
        avg(total_margin) as total_mean,
        percentile_cont(0.5) within group (order by total_margin) as total_median,

        -- Dispersion
        stddev(total_margin) as total_std,
        percentile_cont(0.75) within group (order by total_margin)
            - percentile_cont(0.25) within group (order by total_margin) as total_iqr,

        -- Percentiles
        percentile_cont(0.05) within group (order by total_margin) as total_p5,
        percentile_cont(0.25) within group (order by total_margin) as total_p25,
        percentile_cont(0.75) within group (order by total_margin) as total_p75,
        percentile_cont(0.95) within group (order by total_margin) as total_p95,

        -- Extremes
        min(total_margin) as total_min,
        max(total_margin) as total_max,

        -- Bucket counts
        sum(case when total_bucket = 'within_5' then 1 else 0 end) as total_within_5_count,
        sum(case when total_bucket = 'within_6' then 1 else 0 end) as total_within_6_count,
        sum(case when total_bucket = 'within_8' then 1 else 0 end) as total_within_8_count,
        sum(case when total_bucket = 'within_10' then 1 else 0 end) as total_within_10_count,
        sum(case when total_bucket = 'within_15' then 1 else 0 end) as total_within_15_count,
        sum(case when total_bucket = 'beyond_15' then 1 else 0 end) as total_beyond_15_count,

        -- Rates (exclusive)
        avg(case when abs(total_margin) < 6 then 1.0 else 0.0 end) as total_within_6_rate,
        avg(case when abs(total_margin) < 8 then 1.0 else 0.0 end) as total_within_8_rate,
        avg(case when abs(total_margin) < 10 then 1.0 else 0.0 end) as total_within_10_rate,

        -- Skewness
        case
            when stddev(total_margin) > 0 then
                3.0 * (avg(total_margin) - percentile_cont(0.5) within group (order by total_margin))
                / nullif(stddev(total_margin), 0)
            else 0
        end as total_skewness,

        -- All margins as JSON array
        json_agg(total_margin order by game_date) as total_margins_json

    from total_margins
    group by team_id, team_name, season
),

-- Calculate predictability scores
final as (
    select
        coalesce(s.team_id, t.team_id) as team_id,
        coalesce(s.team_name, t.team_name) as team_name,
        coalesce(s.season, t.season) as season,

        -- Spread distribution
        s.spread_games,
        s.spread_mean,
        s.spread_median,
        s.spread_std,
        s.spread_iqr,
        s.spread_p5,
        s.spread_p25,
        s.spread_p75,
        s.spread_p95,
        s.spread_min,
        s.spread_max,
        s.spread_within_5_count,
        s.spread_within_6_count,
        s.spread_within_8_count,
        s.spread_within_10_count,
        s.spread_within_15_count,
        s.spread_beyond_15_count,
        s.spread_within_6_rate,
        s.spread_within_8_rate,
        s.spread_within_10_rate,
        s.spread_skewness,
        s.spread_margins_json,

        -- Total distribution
        t.total_games,
        t.total_mean,
        t.total_median,
        t.total_std,
        t.total_iqr,
        t.total_p5,
        t.total_p25,
        t.total_p75,
        t.total_p95,
        t.total_min,
        t.total_max,
        t.total_within_5_count,
        t.total_within_6_count,
        t.total_within_8_count,
        t.total_within_10_count,
        t.total_within_15_count,
        t.total_beyond_15_count,
        t.total_within_6_rate,
        t.total_within_8_rate,
        t.total_within_10_rate,
        t.total_skewness,
        t.total_margins_json,

        -- SPREAD PREDICTABILITY SCORE (0-100)
        -- 30% low std + 20% positive kurtosis proxy + 50% within_10_rate
        case
            when s.spread_std is not null and s.spread_within_10_rate is not null then
                least(100, greatest(0,
                    (100 - (s.spread_std - 5) * (100.0 / 15)) * 0.30  -- std component
                    + (50 + coalesce(s.spread_iqr, 10) * (-2)) * 0.20  -- iqr as kurtosis proxy
                    + s.spread_within_10_rate * 100 * 0.50  -- within_10 component
                ))
            else null
        end as spread_predictability,

        -- TOTAL PREDICTABILITY SCORE (0-100)
        case
            when t.total_std is not null and t.total_within_10_rate is not null then
                least(100, greatest(0,
                    (100 - (t.total_std - 5) * (100.0 / 15)) * 0.30
                    + (50 + coalesce(t.total_iqr, 10) * (-2)) * 0.20
                    + t.total_within_10_rate * 100 * 0.50
                ))
            else null
        end as total_predictability,

        -- COMBINED SPREAD EAGLE SCORE
        case
            when s.spread_std is not null and t.total_std is not null then
                (
                    least(100, greatest(0,
                        (100 - (s.spread_std - 5) * (100.0 / 15)) * 0.30
                        + (50 + coalesce(s.spread_iqr, 10) * (-2)) * 0.20
                        + s.spread_within_10_rate * 100 * 0.50
                    ))
                    +
                    least(100, greatest(0,
                        (100 - (t.total_std - 5) * (100.0 / 15)) * 0.30
                        + (50 + coalesce(t.total_iqr, 10) * (-2)) * 0.20
                        + t.total_within_10_rate * 100 * 0.50
                    ))
                ) / 2.0
            else null
        end as spread_eagle_score

    from spread_distribution s
    full outer join total_distribution t
        on s.team_id = t.team_id
        and s.season = t.season
)

select * from final
