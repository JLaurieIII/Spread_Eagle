{{
    config(
        materialized='table'
    )
}}

/*
    ============================================================================
    MART MODEL: fct_cbb__game_dashboard
    ============================================================================

    PURPOSE:
    Single source of truth for the Spread Eagle UI game dashboard.
    Provides ALL data needed to render a game card in one query.

    GRAIN: 1 row per game (with both home and away team stats embedded)

    INCLUDES:
    - Game metadata (date, time, venue, status)
    - Betting lines (spread, total)
    - Team records (overall W-L, conference W-L)
    - ATS records (per team)
    - O/U records (per team)
    - Rolling stats (PPG, pace, etc.)
    - Volatility metrics (teaser survival, stddev)
    - Recent form (last 5 W/L)
    - Last 5 games with results

    USAGE:
    SELECT * FROM fct_cbb__game_dashboard WHERE game_date = '2026-01-24'

    ============================================================================
*/

-- =============================================================================
-- STEP 1: Base games with betting lines
-- =============================================================================
with games_with_lines as (
    select
        g.id as game_id,
        g.start_date::date as game_date,
        to_char(g.start_date, 'HH:MI AM') as game_time,
        g.start_date as game_timestamp,
        g.season,
        g.status,
        g.neutral_site,
        g.conference_game,

        -- Venue
        g.venue,
        g.city,
        g.state,

        -- Home team
        g.home_team_id,
        g.home_team,
        g.home_conference,
        g.home_seed as home_rank,
        g.home_points,

        -- Away team
        g.away_team_id,
        g.away_team,
        g.away_conference,
        g.away_seed as away_rank,
        g.away_points,

        -- Betting lines (prefer Bovada, fall back to consensus)
        coalesce(bl_bovada.spread, bl_consensus.spread) as spread,
        coalesce(bl_bovada.over_under, bl_consensus.over_under) as total,
        coalesce(bl_bovada.home_moneyline, bl_consensus.home_moneyline) as home_ml,
        coalesce(bl_bovada.away_moneyline, bl_consensus.away_moneyline) as away_ml

    from cbb.games g
    left join cbb.betting_lines bl_bovada
        on g.id = bl_bovada.game_id
        and bl_bovada.provider = 'Bovada'
    left join cbb.betting_lines bl_consensus
        on g.id = bl_consensus.game_id
        and bl_consensus.provider = 'consensus'
),

-- =============================================================================
-- STEP 2: Calculate team records (overall W-L) up to each game
-- =============================================================================
team_game_results as (
    select
        g.id as game_id,
        g.start_date::date as game_date,
        g.season,
        g.home_team_id as team_id,
        g.home_team as team_name,
        g.home_conference as conference,
        g.conference_game,
        case when g.home_points > g.away_points then 1 else 0 end as is_win,
        case when g.home_points < g.away_points then 1 else 0 end as is_loss
    from cbb.games g
    where g.status = 'final' and g.home_points is not null

    union all

    select
        g.id as game_id,
        g.start_date::date as game_date,
        g.season,
        g.away_team_id as team_id,
        g.away_team as team_name,
        g.away_conference as conference,
        g.conference_game,
        case when g.away_points > g.home_points then 1 else 0 end as is_win,
        case when g.away_points < g.home_points then 1 else 0 end as is_loss
    from cbb.games g
    where g.status = 'final' and g.away_points is not null
),

team_records as (
    select
        team_id,
        season,
        game_date,
        -- Overall record (games before this date in the season)
        sum(is_win) over w_season_prior as wins,
        sum(is_loss) over w_season_prior as losses,
        -- Conference record
        sum(case when conference_game then is_win else 0 end) over w_season_prior as conf_wins,
        sum(case when conference_game then is_loss else 0 end) over w_season_prior as conf_losses
    from team_game_results
    window w_season_prior as (
        partition by team_id, season
        order by game_date, game_id
        rows between unbounded preceding and 1 preceding
    )
),

-- Deduplicate to get latest record per team per date
team_records_daily as (
    select distinct on (team_id, season, game_date)
        team_id,
        season,
        game_date,
        wins,
        losses,
        conf_wins,
        conf_losses
    from team_records
    order by team_id, season, game_date, wins desc nulls last
),

-- Get the LATEST record for each team (for scheduled games)
team_records_latest as (
    select distinct on (team_id, season)
        team_id,
        season,
        wins,
        losses,
        conf_wins,
        conf_losses
    from team_records
    order by team_id, season, game_date desc, wins desc nulls last
),

-- =============================================================================
-- STEP 3: Calculate ATS records per team
-- =============================================================================
team_ats_results as (
    select
        bl.start_date::date as game_date,
        bl.season,
        bl.home_team_id as team_id,
        case
            when (bl.home_score - bl.away_score) + bl.spread > 0 then 1
            when (bl.home_score - bl.away_score) + bl.spread < 0 then 0
            else null  -- push
        end as ats_win,
        case
            when (bl.home_score - bl.away_score) + bl.spread = 0 then 1
            else 0
        end as ats_push
    from cbb.betting_lines bl
    where bl.provider = 'Bovada'
      and bl.spread is not null
      and bl.home_score is not null
      and bl.home_score > 0

    union all

    select
        bl.start_date::date as game_date,
        bl.season,
        bl.away_team_id as team_id,
        case
            when (bl.away_score - bl.home_score) + (-bl.spread) > 0 then 1
            when (bl.away_score - bl.home_score) + (-bl.spread) < 0 then 0
            else null  -- push
        end as ats_win,
        case
            when (bl.away_score - bl.home_score) + (-bl.spread) = 0 then 1
            else 0
        end as ats_push
    from cbb.betting_lines bl
    where bl.provider = 'Bovada'
      and bl.spread is not null
      and bl.away_score is not null
      and bl.away_score > 0
),

team_ats_records as (
    select
        team_id,
        season,
        game_date,
        sum(ats_win) over w_season_prior as ats_wins,
        sum(case when ats_win = 0 then 1 else 0 end) over w_season_prior as ats_losses,
        sum(ats_push) over w_season_prior as ats_pushes
    from team_ats_results
    where ats_win is not null
    window w_season_prior as (
        partition by team_id, season
        order by game_date
        rows between unbounded preceding and 1 preceding
    )
),

team_ats_daily as (
    select distinct on (team_id, season, game_date)
        team_id,
        season,
        game_date,
        coalesce(ats_wins, 0) as ats_wins,
        coalesce(ats_losses, 0) as ats_losses,
        coalesce(ats_pushes, 0) as ats_pushes
    from team_ats_records
    order by team_id, season, game_date, ats_wins desc nulls last
),

-- Get LATEST ATS record for each team
team_ats_latest as (
    select distinct on (team_id, season)
        team_id,
        season,
        coalesce(ats_wins, 0) as ats_wins,
        coalesce(ats_losses, 0) as ats_losses,
        coalesce(ats_pushes, 0) as ats_pushes
    from team_ats_records
    order by team_id, season, game_date desc, ats_wins desc nulls last
),

-- =============================================================================
-- STEP 4: Calculate O/U records per team
-- =============================================================================
team_ou_results as (
    select
        bl.start_date::date as game_date,
        bl.season,
        bl.home_team_id as team_id,
        case
            when (bl.home_score + bl.away_score) > bl.over_under then 1
            else 0
        end as over_hit,
        case
            when (bl.home_score + bl.away_score) < bl.over_under then 1
            else 0
        end as under_hit,
        case
            when (bl.home_score + bl.away_score) = bl.over_under then 1
            else 0
        end as ou_push
    from cbb.betting_lines bl
    where bl.provider = 'Bovada'
      and bl.over_under is not null
      and bl.home_score is not null
      and bl.home_score > 0

    union all

    select
        bl.start_date::date as game_date,
        bl.season,
        bl.away_team_id as team_id,
        case
            when (bl.home_score + bl.away_score) > bl.over_under then 1
            else 0
        end as over_hit,
        case
            when (bl.home_score + bl.away_score) < bl.over_under then 1
            else 0
        end as under_hit,
        case
            when (bl.home_score + bl.away_score) = bl.over_under then 1
            else 0
        end as ou_push
    from cbb.betting_lines bl
    where bl.provider = 'Bovada'
      and bl.over_under is not null
      and bl.away_score is not null
      and bl.away_score > 0
),

team_ou_records as (
    select
        team_id,
        season,
        game_date,
        sum(over_hit) over w_season_prior as overs,
        sum(under_hit) over w_season_prior as unders,
        sum(ou_push) over w_season_prior as ou_pushes
    from team_ou_results
    window w_season_prior as (
        partition by team_id, season
        order by game_date
        rows between unbounded preceding and 1 preceding
    )
),

team_ou_daily as (
    select distinct on (team_id, season, game_date)
        team_id,
        season,
        game_date,
        coalesce(overs, 0) as overs,
        coalesce(unders, 0) as unders,
        coalesce(ou_pushes, 0) as ou_pushes
    from team_ou_records
    order by team_id, season, game_date, overs desc nulls last
),

-- Get LATEST O/U record for each team
team_ou_latest as (
    select distinct on (team_id, season)
        team_id,
        season,
        coalesce(overs, 0) as overs,
        coalesce(unders, 0) as unders,
        coalesce(ou_pushes, 0) as ou_pushes
    from team_ou_records
    order by team_id, season, game_date desc, overs desc nulls last
),

-- =============================================================================
-- STEP 5: Get last 5 games per team (as JSON array)
-- =============================================================================
team_all_games as (
    select
        g.id as game_id,
        g.start_date::date as game_date,
        g.season,
        g.home_team_id as team_id,
        g.home_team as team_name,
        g.away_team as opponent,
        case when g.home_points > g.away_points then 'W' else 'L' end as result,
        g.home_points || '-' || g.away_points as score,
        case
            when bl.spread is null then null
            else round(((g.home_points - g.away_points) + bl.spread)::numeric, 1)
        end as spread_result
    from cbb.games g
    left join cbb.betting_lines bl
        on g.id = bl.game_id and bl.provider = 'Bovada'
    where g.status = 'final' and g.home_points is not null and g.home_points > 0

    union all

    select
        g.id as game_id,
        g.start_date::date as game_date,
        g.season,
        g.away_team_id as team_id,
        g.away_team as team_name,
        g.home_team as opponent,
        case when g.away_points > g.home_points then 'W' else 'L' end as result,
        g.away_points || '-' || g.home_points as score,
        case
            when bl.spread is null then null
            else round(((g.away_points - g.home_points) + (-bl.spread))::numeric, 1)
        end as spread_result
    from cbb.games g
    left join cbb.betting_lines bl
        on g.id = bl.game_id and bl.provider = 'Bovada'
    where g.status = 'final' and g.away_points is not null and g.away_points > 0
),

team_recent_games as (
    select
        *,
        row_number() over (
            partition by team_id, season
            order by game_date desc, game_id desc
        ) as recency_rank
    from team_all_games
),

team_last5 as (
    select
        team_id,
        season,
        json_agg(
            json_build_object(
                'date', to_char(game_date, 'MM/DD'),
                'opponent', opponent,
                'result', result,
                'score', score,
                'spread_result', spread_result
            )
            order by recency_rank
        ) as last_5_games,
        string_agg(result, '' order by recency_rank) as recent_form
    from team_recent_games
    where recency_rank <= 5
    group by team_id, season
),

-- =============================================================================
-- STEP 6: Get LATEST rolling stats for each team (most recent completed game)
-- =============================================================================
latest_team_rolling as (
    select distinct on (team_id, season)
        team_id,
        season,
        avg_points_scored_l5 as ppg,
        avg_points_allowed_l5 as opp_ppg,
        avg_pace_l5 as pace,
        avg_off_rating_l5 as off_rating,
        avg_def_rating_l5 as def_rating
    from {{ ref('int_cbb__team_rolling_stats') }}
    where games_played_season >= 5  -- need at least 5 games for L5 stats
    order by team_id, season, game_date desc, game_id desc
),

-- =============================================================================
-- STEP 7: Get LATEST volatility stats for each team
-- =============================================================================
latest_team_volatility as (
    select distinct on (team_id, season)
        team_id,
        season,
        stddev_cover_margin_l10 as cover_stddev,
        teaser_8_survival_l10 as teaser8_rate,
        teaser_10_survival_l10 as teaser10_rate,
        ats_win_rate_l10 as ats_rate_l10,
        blowout_rate_l10 as blowout_rate
    from {{ ref('int_cbb__team_spread_volatility') }}
    where games_played >= 5  -- need at least 5 games
    order by team_id, season, game_date desc, game_id desc
),

-- =============================================================================
-- FINAL: Bring it all together
-- =============================================================================
final as (
    select
        -- Game info
        g.game_id,
        g.game_date,
        g.game_time,
        g.game_timestamp,
        g.season,
        g.status,
        g.neutral_site,
        g.conference_game,
        g.venue,
        g.city || ', ' || g.state as location,

        -- Betting lines
        g.spread,
        g.total,
        g.home_ml,
        g.away_ml,

        -- Home team basic info
        g.home_team_id,
        g.home_team,
        g.home_conference,
        g.home_rank,
        g.home_points,

        -- Home team records (use latest if date-specific not available)
        coalesce(hr.wins, hrl.wins, 0) || '-' || coalesce(hr.losses, hrl.losses, 0) as home_record,
        coalesce(hr.conf_wins, hrl.conf_wins, 0) || '-' || coalesce(hr.conf_losses, hrl.conf_losses, 0) as home_conf_record,
        coalesce(hats.ats_wins, hatsl.ats_wins, 0) || '-' || coalesce(hats.ats_losses, hatsl.ats_losses, 0) || '-' || coalesce(hats.ats_pushes, hatsl.ats_pushes, 0) as home_ats_record,
        coalesce(hou.overs, houl.overs, 0) || '-' || coalesce(hou.unders, houl.unders, 0) || '-' || coalesce(hou.ou_pushes, houl.ou_pushes, 0) as home_ou_record,

        -- Home team rolling stats
        round(hroll.ppg::numeric, 1) as home_ppg,
        round(hroll.opp_ppg::numeric, 1) as home_opp_ppg,
        round(hroll.pace::numeric, 1) as home_pace,

        -- Home team volatility
        round(hvol.cover_stddev::numeric, 1) as home_cover_stddev,
        round(hvol.teaser10_rate::numeric, 2) as home_teaser10_rate,

        -- Home team recent games
        hl5.last_5_games as home_last_5_games,
        hl5.recent_form as home_recent_form,

        -- Away team basic info
        g.away_team_id,
        g.away_team,
        g.away_conference,
        g.away_rank,
        g.away_points,

        -- Away team records (use latest if date-specific not available)
        coalesce(ar.wins, arl.wins, 0) || '-' || coalesce(ar.losses, arl.losses, 0) as away_record,
        coalesce(ar.conf_wins, arl.conf_wins, 0) || '-' || coalesce(ar.conf_losses, arl.conf_losses, 0) as away_conf_record,
        coalesce(aats.ats_wins, aatsl.ats_wins, 0) || '-' || coalesce(aats.ats_losses, aatsl.ats_losses, 0) || '-' || coalesce(aats.ats_pushes, aatsl.ats_pushes, 0) as away_ats_record,
        coalesce(aou.overs, aoul.overs, 0) || '-' || coalesce(aou.unders, aoul.unders, 0) || '-' || coalesce(aou.ou_pushes, aoul.ou_pushes, 0) as away_ou_record,

        -- Away team rolling stats
        round(aroll.ppg::numeric, 1) as away_ppg,
        round(aroll.opp_ppg::numeric, 1) as away_opp_ppg,
        round(aroll.pace::numeric, 1) as away_pace,

        -- Away team volatility
        round(avol.cover_stddev::numeric, 1) as away_cover_stddev,
        round(avol.teaser10_rate::numeric, 2) as away_teaser10_rate,

        -- Away team recent games
        al5.last_5_games as away_last_5_games,
        al5.recent_form as away_recent_form,

        -- Combined metrics
        round(((coalesce(hvol.cover_stddev, 15) + coalesce(avol.cover_stddev, 15)) / 2)::numeric, 1) as combined_volatility,
        case
            when (coalesce(hvol.teaser10_rate, 0.8) + coalesce(avol.teaser10_rate, 0.8)) / 2 >= 0.85
                 and (coalesce(hvol.cover_stddev, 15) + coalesce(avol.cover_stddev, 15)) / 2 < 12
            then true
            else false
        end as teaser_friendly,
        case
            when (coalesce(hvol.cover_stddev, 15) + coalesce(avol.cover_stddev, 15)) / 2 < 10 then 'LOW'
            when (coalesce(hvol.cover_stddev, 15) + coalesce(avol.cover_stddev, 15)) / 2 < 14 then 'MED'
            else 'HIGH'
        end as volatility_level

    from games_with_lines g

    -- Home team joins (date-specific)
    left join team_records_daily hr
        on g.home_team_id = hr.team_id
        and g.season = hr.season
        and g.game_date = hr.game_date
    left join team_ats_daily hats
        on g.home_team_id = hats.team_id
        and g.season = hats.season
        and g.game_date = hats.game_date
    left join team_ou_daily hou
        on g.home_team_id = hou.team_id
        and g.season = hou.season
        and g.game_date = hou.game_date
    -- Home team joins (latest - fallback for scheduled games)
    left join team_records_latest hrl
        on g.home_team_id = hrl.team_id
        and g.season = hrl.season
    left join team_ats_latest hatsl
        on g.home_team_id = hatsl.team_id
        and g.season = hatsl.season
    left join team_ou_latest houl
        on g.home_team_id = houl.team_id
        and g.season = houl.season
    left join latest_team_rolling hroll
        on g.home_team_id = hroll.team_id
        and g.season = hroll.season
    left join latest_team_volatility hvol
        on g.home_team_id = hvol.team_id
        and g.season = hvol.season
    left join team_last5 hl5
        on g.home_team_id = hl5.team_id
        and g.season = hl5.season

    -- Away team joins (date-specific)
    left join team_records_daily ar
        on g.away_team_id = ar.team_id
        and g.season = ar.season
        and g.game_date = ar.game_date
    left join team_ats_daily aats
        on g.away_team_id = aats.team_id
        and g.season = aats.season
        and g.game_date = aats.game_date
    left join team_ou_daily aou
        on g.away_team_id = aou.team_id
        and g.season = aou.season
        and g.game_date = aou.game_date
    -- Away team joins (latest - fallback for scheduled games)
    left join team_records_latest arl
        on g.away_team_id = arl.team_id
        and g.season = arl.season
    left join team_ats_latest aatsl
        on g.away_team_id = aatsl.team_id
        and g.season = aatsl.season
    left join team_ou_latest aoul
        on g.away_team_id = aoul.team_id
        and g.season = aoul.season
    left join latest_team_rolling aroll
        on g.away_team_id = aroll.team_id
        and g.season = aroll.season
    left join latest_team_volatility avol
        on g.away_team_id = avol.team_id
        and g.season = avol.season
    left join team_last5 al5
        on g.away_team_id = al5.team_id
        and g.season = al5.season
)

select * from final
order by game_date desc, game_timestamp
