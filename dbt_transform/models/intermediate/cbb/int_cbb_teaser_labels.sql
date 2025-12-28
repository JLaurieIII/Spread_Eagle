{{
    config(
        materialized='view',
        tags=['intermediate', 'cbb', 'labels']
    )
}}

/*
    TEASER LABELS (TARGET VARIABLES)

    Purpose: Calculate what would have happened with various teaser adjustments.
    These are the TARGET LABELS for ML models - computed from actual outcomes.

    Teaser mechanics:
    - Add points to your side of the spread
    - Original spread -5, teaser +6 → adjusted spread +1
    - If cover_margin_team + teaser_points > 0 → teaser wins

    Standard teaser options modeled:
    - +6 points (standard)
    - +7 points (super teaser)
    - +8 points (monster teaser)
    - +10 points (sweetheart teaser)
*/

with team_games as (
    select
        game_id,
        team_id,
        team,
        game_date,
        season,
        team_game_number,
        is_home,
        closing_spread_team,
        cover_margin_team,
        ats_win_team,
        ats_push_flag
    from {{ ref('int_cbb_team_game') }}
),

teaser_labels as (
    select
        game_id,
        team_id,
        team,
        game_date,
        season,
        team_game_number,
        is_home,
        closing_spread_team,
        cover_margin_team,
        ats_win_team,
        ats_push_flag,

        -- =====================================================
        -- TEASER WIN LABELS (BINARY TARGETS)
        -- Did the teaser-adjusted bet win?
        -- =====================================================

        -- +6 point teaser
        case
            when cover_margin_team + 6 > 0 then 1
            when cover_margin_team + 6 < 0 then 0
            else null  -- push
        end as win_teased_6,

        -- +7 point teaser
        case
            when cover_margin_team + 7 > 0 then 1
            when cover_margin_team + 7 < 0 then 0
            else null  -- push
        end as win_teased_7,

        -- +8 point teaser
        case
            when cover_margin_team + 8 > 0 then 1
            when cover_margin_team + 8 < 0 then 0
            else null  -- push
        end as win_teased_8,

        -- +10 point teaser
        case
            when cover_margin_team + 10 > 0 then 1
            when cover_margin_team + 10 < 0 then 0
            else null  -- push
        end as win_teased_10,

        -- =====================================================
        -- TEASER PUSH FLAGS
        -- Did the teaser land exactly on zero?
        -- =====================================================

        case when cover_margin_team + 6 = 0 then true else false end as push_teased_6,
        case when cover_margin_team + 7 = 0 then true else false end as push_teased_7,
        case when cover_margin_team + 8 = 0 then true else false end as push_teased_8,
        case when cover_margin_team + 10 = 0 then true else false end as push_teased_10,

        -- =====================================================
        -- TEASER VALUE METRICS
        -- How much cushion does the teaser provide?
        -- =====================================================

        -- Teased cover margin (how much we won by with teaser)
        cover_margin_team + 6 as teased_margin_6,
        cover_margin_team + 7 as teased_margin_7,
        cover_margin_team + 8 as teased_margin_8,
        cover_margin_team + 10 as teased_margin_10,

        -- =====================================================
        -- FLIP INDICATORS
        -- Did the teaser flip the outcome?
        -- (Original loss → teaser win)
        -- =====================================================

        case
            when ats_win_team = 0 and (cover_margin_team + 6) > 0 then true
            else false
        end as flip_with_6,

        case
            when ats_win_team = 0 and (cover_margin_team + 7) > 0 then true
            else false
        end as flip_with_7,

        case
            when ats_win_team = 0 and (cover_margin_team + 8) > 0 then true
            else false
        end as flip_with_8,

        case
            when ats_win_team = 0 and (cover_margin_team + 10) > 0 then true
            else false
        end as flip_with_10,

        -- =====================================================
        -- NEAR MISS / CLOSE CALL FLAGS
        -- Useful for understanding distribution edges
        -- =====================================================

        -- Close ATS loss (missed cover by 1-5 points)
        case
            when cover_margin_team < 0 and cover_margin_team >= -5 then true
            else false
        end as close_ats_loss,

        -- Blowout ATS loss (missed cover by 10+ points)
        case
            when cover_margin_team <= -10 then true
            else false
        end as blowout_ats_loss,

        -- Would have survived specific teaser but barely (within 1 point)
        case
            when cover_margin_team + 8 > 0 and cover_margin_team + 8 <= 1 then true
            else false
        end as teaser_8_squeaker

    from team_games
    where cover_margin_team is not null
)

select * from teaser_labels
