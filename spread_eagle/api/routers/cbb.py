"""
================================================================================
CBB API Router
================================================================================

Endpoints for serving college basketball games and predictions.

Endpoints:
    GET /cbb/games              - Get games for a specific date
    GET /cbb/dashboard          - Get full game cards for dashboard UI
    GET /cbb/preview/{game_id}  - AI-generated Spread Eagle game preview
    GET /cbb/predictions        - Get predictions for upcoming games
    GET /cbb/predictions/{id}   - Get prediction for specific game
    GET /cbb/probability        - Calculate P(Total > X) for custom threshold

================================================================================
"""

import math
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
import json
import joblib

from spread_eagle.core.database import get_db
from spread_eagle.services.preview_service import PreviewService

router = APIRouter(prefix="/cbb", tags=["College Basketball"])


# =============================================================================
# PREVIEW MODELS
# =============================================================================

class ArticleSource(BaseModel):
    """An article used in preview generation."""
    title: str = ""
    url: str = ""
    snippet: str = ""


class GamePreviewResponse(BaseModel):
    """AI-generated game preview."""
    game_id: int
    game_date: str
    headline: str
    tldr: str
    body: str
    spread_pick: Optional[str] = None
    spread_rationale: Optional[str] = None
    ou_pick: Optional[str] = None
    ou_rationale: Optional[str] = None
    confidence: Optional[str] = None
    key_factors: List[str] = []
    articles_used: List[ArticleSource] = []
    model_used: str = "gpt-4o"
    generated_at: Optional[str] = None
    cached: bool = False


# =============================================================================
# PREVIEW ENDPOINT
# =============================================================================

@router.get(
    "/preview/{game_id}",
    response_model=GamePreviewResponse,
    summary="Get AI-generated game preview",
)
async def get_game_preview(
    game_id: int,
    date: str = Query(
        ...,
        description="Date in YYYY-MM-DD format",
        examples=["2026-01-27"],
    ),
    db: Session = Depends(get_db),
):
    """
    Get the Spread Eagle AI-generated game preview.

    First request triggers generation (~2-5s). Subsequent requests
    serve the cached result instantly.
    """
    try:
        game_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    service = PreviewService(db)
    result = service.get_or_generate_preview(game_id, game_date)

    if result is None:
        raise HTTPException(
            status_code=503,
            detail="Preview generation unavailable. Check OPENAI_API_KEY or game data.",
        )

    # Strip internal metadata before returning
    result.pop("_raw", None)
    result.pop("_tokens_used", None)
    result.pop("_generation_time_ms", None)

    return GamePreviewResponse(**result)


# =============================================================================
# GAMES BY DATE MODELS
# =============================================================================

class TeamInfo(BaseModel):
    """Team information for a game."""
    name: str
    short: str
    record: Optional[str] = None
    rank: Optional[int] = None
    conference: Optional[str] = None
    ats_record: Optional[str] = None  # e.g., "8-4-1" (wins-losses-pushes)
    ou_record: Optional[str] = None   # e.g., "7-5-1" (overs-unders-pushes)


class GameResponse(BaseModel):
    """A single game with betting lines and team info."""
    id: int
    date: str  # YYYY-MM-DD
    startTime: str  # e.g., "7:00 PM"
    home: TeamInfo
    away: TeamInfo
    venue: Optional[str] = None
    spread: Optional[str] = None  # e.g., "UNC -2.5"
    total: Optional[str] = None  # e.g., "O/U 156.5"
    conference: Optional[str] = None  # Primary conference (home team)
    status: str = "scheduled"  # scheduled, in_progress, final
    homeScore: Optional[int] = None
    awayScore: Optional[int] = None


class GamesDateResponse(BaseModel):
    """Response containing games for a specific date."""
    date: str
    count: int
    games: List[GameResponse]


# =============================================================================
# GAMES BY DATE ENDPOINT
# =============================================================================

@router.get(
    "/games",
    response_model=GamesDateResponse,
    summary="Get CBB games for a specific date",
)
async def get_games_by_date(
    date: str = Query(
        ...,
        description="Date in YYYY-MM-DD format",
        examples=["2026-01-15"],
    ),
    db: Session = Depends(get_db),
):
    """
    Get all college basketball games for a specific date.

    Returns game info including:
    - Teams with records and rankings
    - Betting lines (spread, total)
    - Venue and game time
    - Final scores for completed games
    """
    # Parse and validate date
    try:
        game_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Query games for the date with betting lines, team stats, and betting records
    query = text("""
        WITH team_records AS (
            SELECT
                team_id,
                team,
                conference,
                wins,
                losses,
                CONCAT(wins, '-', losses) as record
            FROM cbb.team_season_stats
            WHERE season = (
                SELECT MAX(season) FROM cbb.team_season_stats
            )
        ),
        -- Calculate ATS and O/U records for each team from completed games
        game_betting_results AS (
            SELECT
                g.id as game_id,
                g.home_team_id,
                g.away_team_id,
                g.home_points,
                g.away_points,
                bl.spread,
                bl.over_under,
                -- Home team margin (positive = home won by this much)
                g.home_points - g.away_points as home_margin,
                -- Total points
                g.home_points + g.away_points as total_points
            FROM cbb.games g
            INNER JOIN cbb.betting_lines bl ON g.id = bl.game_id AND bl.provider = 'Bovada'
            WHERE g.home_points IS NOT NULL
              AND g.away_points IS NOT NULL
              AND bl.spread IS NOT NULL
              AND bl.over_under IS NOT NULL
        ),
        team_ats_records AS (
            -- Home team ATS results
            SELECT
                home_team_id as team_id,
                SUM(CASE WHEN home_margin + spread > 0 THEN 1 ELSE 0 END) as ats_wins,
                SUM(CASE WHEN home_margin + spread < 0 THEN 1 ELSE 0 END) as ats_losses,
                SUM(CASE WHEN home_margin + spread = 0 THEN 1 ELSE 0 END) as ats_pushes
            FROM game_betting_results
            GROUP BY home_team_id
            UNION ALL
            -- Away team ATS results (spread is from home perspective, so flip it)
            SELECT
                away_team_id as team_id,
                SUM(CASE WHEN -home_margin - spread > 0 THEN 1 ELSE 0 END) as ats_wins,
                SUM(CASE WHEN -home_margin - spread < 0 THEN 1 ELSE 0 END) as ats_losses,
                SUM(CASE WHEN -home_margin - spread = 0 THEN 1 ELSE 0 END) as ats_pushes
            FROM game_betting_results
            GROUP BY away_team_id
        ),
        team_ats_agg AS (
            SELECT
                team_id,
                SUM(ats_wins) as ats_wins,
                SUM(ats_losses) as ats_losses,
                SUM(ats_pushes) as ats_pushes
            FROM team_ats_records
            GROUP BY team_id
        ),
        team_ou_records AS (
            -- Both home and away teams share the same O/U result per game
            SELECT
                home_team_id as team_id,
                SUM(CASE WHEN total_points > over_under THEN 1 ELSE 0 END) as ou_overs,
                SUM(CASE WHEN total_points < over_under THEN 1 ELSE 0 END) as ou_unders,
                SUM(CASE WHEN total_points = over_under THEN 1 ELSE 0 END) as ou_pushes
            FROM game_betting_results
            GROUP BY home_team_id
            UNION ALL
            SELECT
                away_team_id as team_id,
                SUM(CASE WHEN total_points > over_under THEN 1 ELSE 0 END) as ou_overs,
                SUM(CASE WHEN total_points < over_under THEN 1 ELSE 0 END) as ou_unders,
                SUM(CASE WHEN total_points = over_under THEN 1 ELSE 0 END) as ou_pushes
            FROM game_betting_results
            GROUP BY away_team_id
        ),
        team_ou_agg AS (
            SELECT
                team_id,
                SUM(ou_overs) as ou_overs,
                SUM(ou_unders) as ou_unders,
                SUM(ou_pushes) as ou_pushes
            FROM team_ou_records
            GROUP BY team_id
        )
        SELECT
            g.id,
            g.start_date,
            g.home_team_id,
            g.home_team,
            g.home_conference,
            g.home_points,
            ht.abbreviation as home_abbrev,
            g.away_team_id,
            g.away_team,
            g.away_conference,
            g.away_points,
            at.abbreviation as away_abbrev,
            g.venue,
            g.status,
            bl.spread,
            bl.over_under,
            hr.record as home_record,
            ar.record as away_record,
            -- Home team betting records
            CONCAT(COALESCE(hats.ats_wins, 0), '-', COALESCE(hats.ats_losses, 0), '-', COALESCE(hats.ats_pushes, 0)) as home_ats_record,
            CONCAT(COALESCE(hou.ou_overs, 0), '-', COALESCE(hou.ou_unders, 0), '-', COALESCE(hou.ou_pushes, 0)) as home_ou_record,
            -- Away team betting records
            CONCAT(COALESCE(aats.ats_wins, 0), '-', COALESCE(aats.ats_losses, 0), '-', COALESCE(aats.ats_pushes, 0)) as away_ats_record,
            CONCAT(COALESCE(aou.ou_overs, 0), '-', COALESCE(aou.ou_unders, 0), '-', COALESCE(aou.ou_pushes, 0)) as away_ou_record
        FROM cbb.games g
        LEFT JOIN cbb.teams ht ON g.home_team_id = ht.id
        LEFT JOIN cbb.teams at ON g.away_team_id = at.id
        LEFT JOIN cbb.betting_lines bl
            ON g.id = bl.game_id
            AND bl.provider = 'Bovada'
        LEFT JOIN team_records hr ON g.home_team_id = hr.team_id
        LEFT JOIN team_records ar ON g.away_team_id = ar.team_id
        LEFT JOIN team_ats_agg hats ON g.home_team_id = hats.team_id
        LEFT JOIN team_ou_agg hou ON g.home_team_id = hou.team_id
        LEFT JOIN team_ats_agg aats ON g.away_team_id = aats.team_id
        LEFT JOIN team_ou_agg aou ON g.away_team_id = aou.team_id
        WHERE DATE(g.start_date AT TIME ZONE 'America/New_York') = :game_date
        ORDER BY g.start_date
    """)

    result = db.execute(query, {"game_date": game_date})
    rows = result.fetchall()

    games = []
    for row in rows:
        # Format time (cross-platform compatible)
        if row.start_date:
            hour = row.start_date.hour
            minute = row.start_date.minute
            am_pm = "AM" if hour < 12 else "PM"
            hour_12 = hour % 12 or 12
            start_time = f"{hour_12}:{minute:02d} {am_pm}"
        else:
            start_time = "TBD"

        # Determine status
        if row.home_points is not None and row.away_points is not None:
            status = "final"
        else:
            status = "scheduled"

        # Format spread string (e.g., "UNC -2.5")
        spread_str = None
        if row.spread is not None:
            spread_val = float(row.spread)
            if spread_val < 0:
                # Home team favored
                spread_str = f"{row.home_team} {spread_val}"
            elif spread_val > 0:
                # Away team favored
                spread_str = f"{row.away_team} -{abs(spread_val)}"
            else:
                spread_str = "PICK"

        # Format total string
        total_str = f"O/U {row.over_under}" if row.over_under else None

        # Extract betting records from row (SQLAlchemy Row objects need direct access)
        home_ats = row.home_ats_record
        home_ou = row.home_ou_record
        away_ats = row.away_ats_record
        away_ou = row.away_ou_record

        games.append(GameResponse(
            id=row.id,
            date=game_date.isoformat(),
            startTime=start_time,
            home=TeamInfo(
                name=row.home_team or "TBD",
                short=row.home_abbrev or _get_short_name(row.home_team),
                record=row.home_record,
                conference=row.home_conference,
                ats_record=home_ats if home_ats and home_ats != "0-0-0" else None,
                ou_record=home_ou if home_ou and home_ou != "0-0-0" else None,
            ),
            away=TeamInfo(
                name=row.away_team or "TBD",
                short=row.away_abbrev or _get_short_name(row.away_team),
                record=row.away_record,
                conference=row.away_conference,
                ats_record=away_ats if away_ats and away_ats != "0-0-0" else None,
                ou_record=away_ou if away_ou and away_ou != "0-0-0" else None,
            ),
            venue=row.venue,
            spread=spread_str,
            total=total_str,
            conference=row.home_conference,
            status=status,
            homeScore=row.home_points,
            awayScore=row.away_points,
        ))

    return GamesDateResponse(
        date=game_date.isoformat(),
        count=len(games),
        games=games,
    )


def _get_short_name(team_name: Optional[str]) -> str:
    """Extract short name from team name."""
    if not team_name:
        return "TBD"

    # Common abbreviations
    abbreviations = {
        "North Carolina": "UNC",
        "North Carolina State": "NCST",
        "South Carolina": "SCAR",
        "Southern California": "USC",
        "Connecticut": "UCONN",
        "Massachusetts": "UMASS",
        "Mississippi": "OLE MISS",
        "Mississippi State": "MSST",
        "Louisiana State": "LSU",
        "Texas A&M": "TAMU",
        "Texas Christian": "TCU",
        "Brigham Young": "BYU",
        "Southern Methodist": "SMU",
        "Central Florida": "UCF",
        "Virginia Tech": "VT",
        "Georgia Tech": "GT",
        "Florida State": "FSU",
        "Ohio State": "OSU",
        "Oklahoma State": "OKST",
        "Michigan State": "MSU",
        "Penn State": "PSU",
        "Iowa State": "ISU",
        "Kansas State": "KSU",
        "Arizona State": "ASU",
        "Washington State": "WSU",
        "Oregon State": "ORST",
        "San Diego State": "SDSU",
        "Boise State": "BSU",
        "Fresno State": "FRES",
        "Colorado State": "CSU",
    }

    for full, abbr in abbreviations.items():
        if full.lower() in team_name.lower():
            return abbr

    # Default: take first word or first 4 letters
    words = team_name.split()
    if len(words) == 1:
        return team_name[:4].upper()
    return words[0].upper()[:6]


# =============================================================================
# DASHBOARD MODELS
# =============================================================================

class DashboardGameResult(BaseModel):
    """Single game result for last 5 games."""
    date: str
    opponent: str
    isHome: bool = True  # True if team was home, False if away
    result: str  # "W" or "L"
    score: str
    spread: Optional[float] = None  # Closing spread (from team's perspective)
    total: Optional[float] = None  # Closing O/U line
    spreadResult: float
    ouResult: Optional[str] = None  # "O", "U", "P", or null
    totalMargin: Optional[float] = None  # Actual total minus line (positive = over)


class TeaserProfile(BaseModel):
    """Historical teaser survival and spread stability metrics."""
    teaser8SurvivalRate: Optional[float] = None
    teaser10SurvivalRate: Optional[float] = None
    within5Rate: Optional[float] = None
    within7Rate: Optional[float] = None
    within10Rate: Optional[float] = None
    blowoutRate: Optional[float] = None
    worstCover: Optional[float] = None
    coverStddev: Optional[float] = None


class OverUnderProfile(BaseModel):
    """Historical over/under trends for a team."""
    overRateL10: Optional[float] = None
    underRateL10: Optional[float] = None
    avgTotalMarginL10: Optional[float] = None
    avgGameTotalL10: Optional[float] = None
    oversLast3: Optional[int] = None
    undersLast3: Optional[int] = None
    # Tightness to total metrics
    within5TotalRate: Optional[float] = None
    within7TotalRate: Optional[float] = None
    within10TotalRate: Optional[float] = None


class TeamDistributionData(BaseModel):
    """Distribution data for KDE visualization."""
    margins: List[float]  # Raw margins for frontend KDE calculation
    mean: float
    median: float
    std: float
    iqr: float
    p5: float
    p25: float
    p75: float
    p95: float
    minVal: float
    maxVal: float
    within8Rate: float  # EXCLUSIVE: < 8
    within10Rate: float  # EXCLUSIVE: < 10
    skewness: float
    predictability: float  # 0-100 score


# =============================================================================
# MARGIN THEATER MODELS (for interactive filtering of distributions)
# =============================================================================

class MarginDataPoint(BaseModel):
    """Single margin with full situational context for Margin Theater."""
    margin: float
    isHome: bool
    isFavorite: bool
    isConference: bool
    prevResult: Optional[str] = None  # "W", "L", or None
    restDays: Optional[int] = None    # 0, 1, 2, 3 (capped at 3)


class TheaterDistributionData(BaseModel):
    """Rich distribution data for Margin Theater feature."""
    dataPoints: List[MarginDataPoint]
    # Baseline stats (unfiltered) for reference
    mean: float
    std: float
    predictability: float
    count: int


class DashboardTeamData(BaseModel):
    """Complete team data for dashboard card."""
    name: str
    shortName: str
    primaryColor: str
    secondaryColor: str = "#ffffff"
    record: str
    rank: Optional[int] = None
    confRecord: str
    conference: str
    atsRecord: str
    ouRecord: str
    ppg: Optional[float] = None
    oppPpg: Optional[float] = None
    pace: Optional[float] = None
    recentForm: List[str]  # ["W", "L", "W", ...]
    last5Games: List[DashboardGameResult]
    # Market variance fields
    spreadVarianceBucket: int = 3
    totalVarianceBucket: int = 3
    spreadVarianceLabel: str = "MED"
    totalVarianceLabel: str = "MED"
    archetype: str = "Neutral"
    spreadMeanError: float = 0.0
    totalMeanError: float = 0.0
    totalRmsStabilized: float = 12.0
    # Teaser profile (historical spread stability)
    teaserProfile: Optional[TeaserProfile] = None
    # Over/Under profile (historical O/U trends)
    overUnderProfile: Optional[OverUnderProfile] = None
    # Distribution data for KDE graphs (shown below last 5 games)
    spreadDistribution: Optional[TeamDistributionData] = None
    totalDistribution: Optional[TeamDistributionData] = None
    # Margin Theater data (interactive filter distributions)
    spreadTheater: Optional[TheaterDistributionData] = None
    totalTheater: Optional[TheaterDistributionData] = None


class DashboardGame(BaseModel):
    """Full game card data for dashboard."""
    id: int
    gameDate: str  # "Sat, Jan 24"
    gameTime: str  # "8:30pm"
    venue: str
    location: str
    spread: Optional[str] = None  # "ALA -3.5"
    total: Optional[str] = None  # "167.5"
    homeTeam: DashboardTeamData
    awayTeam: DashboardTeamData
    league: str = "NCAA"
    # Chaos / teaser fields
    chaosRating: float = 3.0
    chaosLabel: str = "MODERATE"
    teaserUnder8Prob: Optional[float] = None
    teaserUnder10Prob: Optional[float] = None
    edgeSummary: List[str] = []
    # Combined historical teaser metrics
    combinedTeaser8Rate: Optional[float] = None
    combinedTeaser10Rate: Optional[float] = None
    combinedWithin10Rate: Optional[float] = None
    # Combined historical O/U metrics
    combinedOverRateL10: Optional[float] = None
    combinedUnderRateL10: Optional[float] = None
    combinedAvgTotalMargin: Optional[float] = None
    combinedWithin10TotalRate: Optional[float] = None
    # Spread Eagle predictability scores (from KDE analysis)
    spreadPredictability: Optional[float] = None  # Combined spread predictability (0-100)
    totalPredictability: Optional[float] = None  # Combined total predictability (0-100)
    spreadEagleScore: Optional[float] = None  # Average of spread + total (0-100)
    spreadEagleVerdict: str = "N/A"  # "SPREAD EAGLE", "LEAN TEASER", "CAUTION", "AVOID"


class DashboardResponse(BaseModel):
    """Response for dashboard endpoint."""
    date: str
    count: int
    games: List[DashboardGame]


# =============================================================================
# DASHBOARD ENDPOINT
# =============================================================================

# Team primary colors - could move to DB later
TEAM_COLORS = {
    "Alabama": "#9E1B32",
    "Arizona": "#003366",
    "Arkansas": "#9D2235",
    "Auburn": "#0C2340",
    "Baylor": "#154734",
    "BYU": "#002E5D",
    "Cincinnati": "#E00122",
    "Colorado": "#CFB87C",
    "Connecticut": "#000E2F",
    "Creighton": "#005CA9",
    "Duke": "#003087",
    "Florida": "#0021A5",
    "Gonzaga": "#002967",
    "Houston": "#C8102E",
    "Illinois": "#E84A27",
    "Indiana": "#990000",
    "Iowa": "#FFCD00",
    "Iowa State": "#C8102E",
    "Kansas": "#0051BA",
    "Kansas State": "#512888",
    "Kentucky": "#0033A0",
    "Louisville": "#AD0000",
    "LSU": "#461D7C",
    "Marquette": "#003366",
    "Maryland": "#E03A3E",
    "Memphis": "#003087",
    "Miami": "#F47321",
    "Michigan": "#FFCB05",
    "Michigan State": "#18453B",
    "Mississippi State": "#660000",
    "Missouri": "#F1B82D",
    "North Carolina": "#7BAFD4",
    "NC State": "#CC0000",
    "Notre Dame": "#0C2340",
    "Ohio State": "#BB0000",
    "Oklahoma": "#841617",
    "Oklahoma State": "#FF7300",
    "Ole Miss": "#CE1126",
    "Oregon": "#154733",
    "Penn State": "#041E42",
    "Purdue": "#CEB888",
    "Rutgers": "#CC0033",
    "Saint John's": "#C8102E",
    "San Diego State": "#A6192E",
    "South Carolina": "#73000A",
    "St. John's": "#C8102E",
    "Syracuse": "#F76900",
    "TCU": "#4D1979",
    "Tennessee": "#FF8200",
    "Texas": "#BF5700",
    "Texas A&M": "#500000",
    "Texas Tech": "#CC0000",
    "UCLA": "#2D68C4",
    "USC": "#990000",
    "Vanderbilt": "#CFAE70",
    "Villanova": "#00205B",
    "Virginia": "#232D4B",
    "Virginia Tech": "#630031",
    "Wake Forest": "#9E7E38",
    "West Virginia": "#002855",
    "Wisconsin": "#C5050C",
    "Xavier": "#0C2340",
}


def _get_team_color(team_name: str) -> str:
    """Get team primary color, default to a neutral color."""
    return TEAM_COLORS.get(team_name, "#4a5568")


def _get_team_info_from_db(db: Session, team_name: str) -> tuple[str, str, str]:
    """Get team display name, primary color, and secondary color from database."""
    # Order by best match: exact school match first, then display_name prefix
    result = db.execute(
        text("""
            SELECT display_name, primary_color, secondary_color
            FROM cbb.teams
            WHERE display_name = :team_name
               OR school = :team_name
               OR display_name ILIKE :team_pattern
            ORDER BY
                CASE
                    WHEN school = :team_name THEN 1
                    WHEN display_name = :team_name THEN 2
                    ELSE 3
                END
            LIMIT 1
        """),
        {"team_name": team_name, "team_pattern": f"{team_name}%"}
    ).fetchone()

    if result and result[0]:
        display_name = result[0]
        primary = f"#{result[1]}" if result[1] and not result[1].startswith("#") else (result[1] or "#4a5568")
        secondary = f"#{result[2]}" if result[2] and not result[2].startswith("#") else (result[2] or "#ffffff")
        return display_name, primary, secondary

    # Fallback
    return team_name, TEAM_COLORS.get(team_name, "#4a5568"), "#ffffff"


def _get_team_colors_from_db(db: Session, team_name: str) -> tuple[str, str]:
    """Get team primary and secondary colors from database."""
    _, primary, secondary = _get_team_info_from_db(db, team_name)
    return primary, secondary


def _normal_cdf(x: float) -> float:
    """Standard normal CDF using math.erfc (no scipy needed)."""
    return 0.5 * math.erfc(-x / math.sqrt(2))


def _bucket_to_label(bucket: int) -> str:
    """Convert variance bucket (1-5) to human label."""
    if bucket <= 2:
        return "LOW"
    elif bucket <= 3:
        return "MED"
    return "HIGH"


def _bucket_to_archetype(bucket: int) -> str:
    """Convert total variance bucket to team archetype."""
    if bucket <= 2:
        return "Market Follower"
    elif bucket <= 3:
        return "Neutral"
    return "Chaos Team"


def _format_game_date(dt: datetime) -> str:
    """Format datetime to 'Sat, Jan 24' format."""
    return dt.strftime("%a, %b %d").replace(" 0", " ")


def _format_game_time(dt: datetime) -> str:
    """Format datetime to '8:30pm' format."""
    hour = dt.hour
    minute = dt.minute
    am_pm = "am" if hour < 12 else "pm"
    hour_12 = hour % 12 or 12
    if minute == 0:
        return f"{hour_12}{am_pm}"
    return f"{hour_12}:{minute:02d}{am_pm}"


def _get_team_distribution(db: Session, team_id: int, margin_type: str) -> Optional[TeamDistributionData]:
    """
    Get distribution data for a team for KDE visualization.

    Args:
        db: Database session
        team_id: Team ID
        margin_type: "spread" for cover_margin, "total" for total_margin

    Returns:
        TeamDistributionData with raw margins and stats, or None if insufficient data
    """
    if margin_type == "spread":
        table = "intermediate_cbb.int_cbb__team_spread_volatility"
        margin_col = "cover_margin"
    else:
        table = "intermediate_cbb.int_cbb__team_ou_trends"
        margin_col = "total_margin"

    query = text(f"""
        SELECT {margin_col} as margin
        FROM {table}
        WHERE team_id = :team_id
          AND season = 2026
          AND {margin_col} IS NOT NULL
        ORDER BY game_date
    """)

    try:
        result = db.execute(query, {"team_id": team_id}).fetchall()
    except Exception:
        return None

    if len(result) < 5:
        return None

    margins = [float(r.margin) for r in result]
    margins_arr = np.array(margins)

    mean = float(np.mean(margins_arr))
    median = float(np.median(margins_arr))
    std = float(np.std(margins_arr))
    p5, p25, p75, p95 = [float(np.percentile(margins_arr, p)) for p in [5, 25, 75, 95]]
    iqr = p75 - p25

    # EXCLUSIVE comparisons (< not <=) per SESSION_NOTES.md
    within_8 = float(np.mean(np.abs(margins_arr) < 8))
    within_10 = float(np.mean(np.abs(margins_arr) < 10))

    # Skewness approximation (Pearson's second coefficient)
    skewness = 3 * (mean - median) / std if std > 0 else 0

    # Predictability score formula from SESSION_NOTES.md
    # 30% low std + 20% IQR as kurtosis proxy + 50% within_10_rate
    std_score = max(0, min(100, 100 - (std - 5) * (100 / 15)))
    iqr_score = max(0, min(100, 50 - iqr * 2))
    w10_score = within_10 * 100
    predictability = std_score * 0.3 + iqr_score * 0.2 + w10_score * 0.5

    return TeamDistributionData(
        margins=margins,
        mean=round(mean, 2),
        median=round(median, 2),
        std=round(std, 2),
        iqr=round(iqr, 2),
        p5=round(p5, 2),
        p25=round(p25, 2),
        p75=round(p75, 2),
        p95=round(p95, 2),
        minVal=round(float(np.min(margins_arr)), 2),
        maxVal=round(float(np.max(margins_arr)), 2),
        within8Rate=round(within_8, 3),
        within10Rate=round(within_10, 3),
        skewness=round(skewness, 3),
        predictability=round(predictability, 1)
    )


def _get_theater_distribution(
    db: Session,
    team_id: int,
    margin_type: str  # "spread" or "total"
) -> Optional[TheaterDistributionData]:
    """
    Get rich margin data from int_cbb__margin_theater for interactive filtering.

    Args:
        db: Database session
        team_id: Team ID
        margin_type: "spread" for cover_margin, "total" for total_margin

    Returns:
        TheaterDistributionData with data points and baseline stats, or None if insufficient data
    """
    margin_col = "cover_margin" if margin_type == "spread" else "total_margin"

    query = text(f"""
        SELECT
            {margin_col} as margin,
            is_home,
            is_favorite,
            is_conference_game,
            prev_game_result,
            LEAST(rest_days, 3) as rest_days
        FROM intermediate_cbb.int_cbb__margin_theater
        WHERE team_id = :team_id
          AND season = 2026
          AND {margin_col} IS NOT NULL
        ORDER BY game_date
    """)

    try:
        result = db.execute(query, {"team_id": team_id}).fetchall()
    except Exception:
        return None

    if len(result) < 5:
        return None

    data_points = [
        MarginDataPoint(
            margin=float(r.margin),
            isHome=bool(r.is_home),
            isFavorite=bool(r.is_favorite),
            isConference=bool(r.is_conference_game) if r.is_conference_game is not None else False,
            prevResult=r.prev_game_result,
            restDays=int(r.rest_days) if r.rest_days is not None else None
        )
        for r in result
    ]

    margins = [dp.margin for dp in data_points]
    margins_arr = np.array(margins)
    mean = float(np.mean(margins_arr))
    std = float(np.std(margins_arr))
    within_10 = float(np.mean(np.abs(margins_arr) < 10))

    # Predictability score (simplified formula: 50% std, 50% within_10)
    std_score = max(0, min(100, 100 - (std - 5) * (100 / 15)))
    w10_score = within_10 * 100
    predictability = std_score * 0.5 + w10_score * 0.5

    return TheaterDistributionData(
        dataPoints=data_points,
        mean=round(mean, 2),
        std=round(std, 2),
        predictability=round(predictability, 1),
        count=len(data_points)
    )


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Get full game cards for dashboard UI",
)
async def get_dashboard_games(
    date: str = Query(
        ...,
        description="Date in YYYY-MM-DD format",
        examples=["2026-01-24"],
    ),
    db: Session = Depends(get_db),
):
    """
    Get complete game card data for the dashboard UI.

    Returns all games for the date with:
    - Team names, logos, colors
    - Betting lines (spread, total)
    - Records (overall, conference, ATS, O/U)
    - Rolling stats (PPG, OPP PPG, pace)
    - Recent form (last 5 W/L)
    - Last 5 game details with spread results

    Data comes from the dbt mart model fct_cbb__game_dashboard.
    """
    # Parse and validate date
    try:
        game_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Query the dbt mart model
    query = text("""
        SELECT
            game_id,
            game_date,
            game_time,
            game_timestamp,
            venue,
            location,

            -- Home team
            home_team,
            home_abbrev,
            home_team_id,
            home_conference,
            home_record,
            home_conf_record,
            home_ats_record,
            home_ou_record,
            home_ppg,
            home_opp_ppg,
            home_pace,
            home_recent_form,
            home_last_5_games,

            -- Away team
            away_team,
            away_abbrev,
            away_team_id,
            away_conference,
            away_record,
            away_conf_record,
            away_ats_record,
            away_ou_record,
            away_ppg,
            away_opp_ppg,
            away_pace,
            away_recent_form,
            away_last_5_games,

            -- Betting
            spread,
            total,

            -- Home team teaser/volatility metrics
            home_teaser8_rate,
            home_teaser10_rate,
            home_within_5_rate,
            home_within_7_rate,
            home_within_10_rate,
            home_blowout_rate,
            home_worst_cover,
            home_cover_stddev,

            -- Away team teaser/volatility metrics
            away_teaser8_rate,
            away_teaser10_rate,
            away_within_5_rate,
            away_within_7_rate,
            away_within_10_rate,
            away_blowout_rate,
            away_worst_cover,
            away_cover_stddev,

            -- Combined teaser metrics
            combined_teaser8_rate,
            combined_teaser10_rate,
            combined_within_10_rate,

            -- Home team O/U trends
            home_over_rate_l10,
            home_under_rate_l10,
            home_avg_total_margin_l10,
            home_avg_game_total_l10,
            home_overs_last_3,
            home_unders_last_3,

            -- Away team O/U trends
            away_over_rate_l10,
            away_under_rate_l10,
            away_avg_total_margin_l10,
            away_avg_game_total_l10,
            away_overs_last_3,
            away_unders_last_3,

            -- Home team total tightness
            home_within_5_total_rate,
            home_within_7_total_rate,
            home_within_10_total_rate,

            -- Away team total tightness
            away_within_5_total_rate,
            away_within_7_total_rate,
            away_within_10_total_rate,

            -- Combined O/U metrics
            combined_over_rate_l10,
            combined_under_rate_l10,
            combined_avg_total_margin,
            combined_within_10_total_rate,

            -- Market variance buckets (for chaos ratings)
            home_spread_variance_bucket,
            home_total_variance_bucket,
            away_spread_variance_bucket,
            away_total_variance_bucket,
            home_spread_mean_error,
            home_total_mean_error,
            away_spread_mean_error,
            away_total_mean_error,
            home_total_rms_stabilized,
            away_total_rms_stabilized

        FROM marts_cbb.fct_cbb__game_dashboard
        WHERE DATE(game_date) = :game_date
        ORDER BY game_timestamp, game_id
    """)

    try:
        result = db.execute(query, {"game_date": game_date})
        rows = result.fetchall()
    except Exception as e:
        print(f"Dashboard query error for {game_date}: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

    # Helper functions for parsing
    def parse_form(form_str: Optional[str]) -> List[str]:
        """Parse recent form (stored as string like 'WWLWL')."""
        if not form_str:
            return []
        # Take last 5 characters and split into individual W/L
        return list(form_str[-5:]) if form_str else []

    def parse_last_5(games_json) -> List[DashboardGameResult]:
        """Parse last 5 games (stored as JSON array)."""
        if not games_json:
            return []
        try:
            games_list = games_json if isinstance(games_json, list) else json.loads(games_json)
            results = []
            for g in games_list[:5]:
                # Format score to remove decimals if present
                score = g.get("score", "")
                if score:
                    # Convert "80.0-78.0" to "80-78"
                    parts = score.split("-")
                    if len(parts) == 2:
                        try:
                            score = f"{int(float(parts[0]))}-{int(float(parts[1]))}"
                        except ValueError:
                            pass

                results.append(DashboardGameResult(
                    date=g.get("date", ""),
                    opponent=g.get("opponent", ""),
                    isHome=g.get("is_home", True),
                    result=g.get("result", ""),
                    score=score,
                    spread=float(g.get("spread")) if g.get("spread") is not None else None,
                    total=float(g.get("total")) if g.get("total") is not None else None,
                    spreadResult=float(g.get("spread_result", 0) or 0),
                    ouResult=g.get("ou_result"),
                    totalMargin=float(g.get("total_margin")) if g.get("total_margin") is not None else None,
                ))
            return results
        except (json.JSONDecodeError, TypeError):
            return []

    games = []
    for row in rows:
        # Use pre-formatted date/time from dbt mart (already in Eastern timezone)
        if row.game_date:
            game_date_str = _format_game_date(datetime.combine(row.game_date, datetime.min.time()))
        else:
            game_date_str = "TBD"

        # Use game_time from mart (already formatted in Eastern) or format from timestamp
        game_time_str = row.game_time.strip() if row.game_time else "TBD"
        # Convert "07:00 PM" format to "7pm" format
        if game_time_str != "TBD":
            try:
                t = datetime.strptime(game_time_str, "%I:%M %p")
                game_time_str = _format_game_time(t)
            except ValueError:
                pass  # Keep original format if parsing fails

        # Format spread string (use abbreviation from database if available)
        home_short = getattr(row, 'home_abbrev', None) or _get_short_name(row.home_team)
        away_short = getattr(row, 'away_abbrev', None) or _get_short_name(row.away_team)

        spread_str = None
        if row.spread is not None:
            spread_val = float(row.spread)
            if spread_val < 0:
                spread_str = f"{home_short} {spread_val}"
            elif spread_val > 0:
                spread_str = f"{away_short} -{abs(spread_val)}"
            else:
                spread_str = "PICK"

        # Format total
        total_str = str(row.total) if row.total else None

        # Market variance fields (use getattr for backward compatibility - columns may not exist yet)
        h_spread_bucket = int(getattr(row, 'home_spread_variance_bucket', None) or 3)
        h_total_bucket = int(getattr(row, 'home_total_variance_bucket', None) or 3)
        a_spread_bucket = int(getattr(row, 'away_spread_variance_bucket', None) or 3)
        a_total_bucket = int(getattr(row, 'away_total_variance_bucket', None) or 3)
        h_spread_me = float(getattr(row, 'home_spread_mean_error', None) or 0)
        h_total_me = float(getattr(row, 'home_total_mean_error', None) or 0)
        a_spread_me = float(getattr(row, 'away_spread_mean_error', None) or 0)
        a_total_me = float(getattr(row, 'away_total_mean_error', None) or 0)
        h_total_rms = float(getattr(row, 'home_total_rms_stabilized', None) or 12)
        a_total_rms = float(getattr(row, 'away_total_rms_stabilized', None) or 12)

        # Build teaser profiles for each team (historical spread stability metrics)
        home_teaser_profile = None
        if getattr(row, 'home_teaser8_rate', None) is not None:
            home_teaser_profile = TeaserProfile(
                teaser8SurvivalRate=float(row.home_teaser8_rate) if row.home_teaser8_rate is not None else None,
                teaser10SurvivalRate=float(row.home_teaser10_rate) if row.home_teaser10_rate is not None else None,
                within5Rate=float(row.home_within_5_rate) if row.home_within_5_rate is not None else None,
                within7Rate=float(row.home_within_7_rate) if row.home_within_7_rate is not None else None,
                within10Rate=float(row.home_within_10_rate) if row.home_within_10_rate is not None else None,
                blowoutRate=float(row.home_blowout_rate) if row.home_blowout_rate is not None else None,
                worstCover=float(row.home_worst_cover) if row.home_worst_cover is not None else None,
                coverStddev=float(row.home_cover_stddev) if row.home_cover_stddev is not None else None,
            )

        away_teaser_profile = None
        if getattr(row, 'away_teaser8_rate', None) is not None:
            away_teaser_profile = TeaserProfile(
                teaser8SurvivalRate=float(row.away_teaser8_rate) if row.away_teaser8_rate is not None else None,
                teaser10SurvivalRate=float(row.away_teaser10_rate) if row.away_teaser10_rate is not None else None,
                within5Rate=float(row.away_within_5_rate) if row.away_within_5_rate is not None else None,
                within7Rate=float(row.away_within_7_rate) if row.away_within_7_rate is not None else None,
                within10Rate=float(row.away_within_10_rate) if row.away_within_10_rate is not None else None,
                blowoutRate=float(row.away_blowout_rate) if row.away_blowout_rate is not None else None,
                worstCover=float(row.away_worst_cover) if row.away_worst_cover is not None else None,
                coverStddev=float(row.away_cover_stddev) if row.away_cover_stddev is not None else None,
            )

        # Build O/U profiles for each team (historical over/under trends)
        home_ou_profile = None
        if getattr(row, 'home_over_rate_l10', None) is not None:
            home_ou_profile = OverUnderProfile(
                overRateL10=float(row.home_over_rate_l10) if row.home_over_rate_l10 is not None else None,
                underRateL10=float(row.home_under_rate_l10) if row.home_under_rate_l10 is not None else None,
                avgTotalMarginL10=float(row.home_avg_total_margin_l10) if row.home_avg_total_margin_l10 is not None else None,
                avgGameTotalL10=float(row.home_avg_game_total_l10) if row.home_avg_game_total_l10 is not None else None,
                oversLast3=int(row.home_overs_last_3) if row.home_overs_last_3 is not None else None,
                undersLast3=int(row.home_unders_last_3) if row.home_unders_last_3 is not None else None,
                within5TotalRate=float(row.home_within_5_total_rate) if getattr(row, 'home_within_5_total_rate', None) is not None else None,
                within7TotalRate=float(row.home_within_7_total_rate) if getattr(row, 'home_within_7_total_rate', None) is not None else None,
                within10TotalRate=float(row.home_within_10_total_rate) if getattr(row, 'home_within_10_total_rate', None) is not None else None,
            )

        away_ou_profile = None
        if getattr(row, 'away_over_rate_l10', None) is not None:
            away_ou_profile = OverUnderProfile(
                overRateL10=float(row.away_over_rate_l10) if row.away_over_rate_l10 is not None else None,
                underRateL10=float(row.away_under_rate_l10) if row.away_under_rate_l10 is not None else None,
                avgTotalMarginL10=float(row.away_avg_total_margin_l10) if row.away_avg_total_margin_l10 is not None else None,
                avgGameTotalL10=float(row.away_avg_game_total_l10) if row.away_avg_game_total_l10 is not None else None,
                oversLast3=int(row.away_overs_last_3) if row.away_overs_last_3 is not None else None,
                undersLast3=int(row.away_unders_last_3) if row.away_unders_last_3 is not None else None,
                within5TotalRate=float(row.away_within_5_total_rate) if getattr(row, 'away_within_5_total_rate', None) is not None else None,
                within7TotalRate=float(row.away_within_7_total_rate) if getattr(row, 'away_within_7_total_rate', None) is not None else None,
                within10TotalRate=float(row.away_within_10_total_rate) if getattr(row, 'away_within_10_total_rate', None) is not None else None,
            )

        # Fetch distribution data for KDE graphs (shown below last 5 games)
        home_spread_dist = _get_team_distribution(db, row.home_team_id, "spread")
        home_total_dist = _get_team_distribution(db, row.home_team_id, "total")
        away_spread_dist = _get_team_distribution(db, row.away_team_id, "spread")
        away_total_dist = _get_team_distribution(db, row.away_team_id, "total")

        # Fetch Margin Theater distribution data (interactive filtering)
        home_spread_theater = _get_theater_distribution(db, row.home_team_id, "spread")
        home_total_theater = _get_theater_distribution(db, row.home_team_id, "total")
        away_spread_theater = _get_theater_distribution(db, row.away_team_id, "spread")
        away_total_theater = _get_theater_distribution(db, row.away_team_id, "total")

        # Get full team info (display name with mascot, colors)
        home_display_name, home_primary, home_secondary = _get_team_info_from_db(db, row.home_team)
        away_display_name, away_primary, away_secondary = _get_team_info_from_db(db, row.away_team)

        # Build home team data (records are already formatted as strings like "12-5")
        home_team = DashboardTeamData(
            name=home_display_name,
            shortName=home_short,
            primaryColor=home_primary,
            secondaryColor=home_secondary,
            record=row.home_record or "0-0",
            confRecord=row.home_conf_record or "0-0",
            conference=row.home_conference or "",
            atsRecord=row.home_ats_record or "0-0",
            ouRecord=row.home_ou_record or "0-0",
            ppg=round(row.home_ppg, 1) if row.home_ppg else None,
            oppPpg=round(row.home_opp_ppg, 1) if row.home_opp_ppg else None,
            pace=round(row.home_pace, 1) if row.home_pace else None,
            recentForm=parse_form(row.home_recent_form),
            last5Games=parse_last_5(row.home_last_5_games),
            spreadVarianceBucket=h_spread_bucket,
            totalVarianceBucket=h_total_bucket,
            spreadVarianceLabel=_bucket_to_label(h_spread_bucket),
            totalVarianceLabel=_bucket_to_label(h_total_bucket),
            archetype=_bucket_to_archetype(h_total_bucket),
            spreadMeanError=round(h_spread_me, 2),
            totalMeanError=round(h_total_me, 2),
            totalRmsStabilized=round(h_total_rms, 2),
            teaserProfile=home_teaser_profile,
            overUnderProfile=home_ou_profile,
            spreadDistribution=home_spread_dist,
            totalDistribution=home_total_dist,
            spreadTheater=home_spread_theater,
            totalTheater=home_total_theater,
        )

        # Build away team data
        away_team = DashboardTeamData(
            name=away_display_name,
            shortName=away_short,
            primaryColor=away_primary,
            secondaryColor=away_secondary,
            record=row.away_record or "0-0",
            confRecord=row.away_conf_record or "0-0",
            conference=row.away_conference or "",
            atsRecord=row.away_ats_record or "0-0",
            ouRecord=row.away_ou_record or "0-0",
            ppg=round(row.away_ppg, 1) if row.away_ppg else None,
            oppPpg=round(row.away_opp_ppg, 1) if row.away_opp_ppg else None,
            pace=round(row.away_pace, 1) if row.away_pace else None,
            recentForm=parse_form(row.away_recent_form),
            last5Games=parse_last_5(row.away_last_5_games),
            spreadVarianceBucket=a_spread_bucket,
            totalVarianceBucket=a_total_bucket,
            spreadVarianceLabel=_bucket_to_label(a_spread_bucket),
            totalVarianceLabel=_bucket_to_label(a_total_bucket),
            archetype=_bucket_to_archetype(a_total_bucket),
            spreadMeanError=round(a_spread_me, 2),
            totalMeanError=round(a_total_me, 2),
            totalRmsStabilized=round(a_total_rms, 2),
            teaserProfile=away_teaser_profile,
            overUnderProfile=away_ou_profile,
            spreadDistribution=away_spread_dist,
            totalDistribution=away_total_dist,
            spreadTheater=away_spread_theater,
            totalTheater=away_total_theater,
        )

        # ---- Game-level chaos and teaser calculations ----
        chaos_rating = round((h_total_bucket + a_total_bucket) / 2, 1)
        if chaos_rating <= 2:
            chaos_label = "STABLE"
        elif chaos_rating <= 3:
            chaos_label = "MODERATE"
        else:
            chaos_label = "VOLATILE"

        # Teaser probability: P(total < line + k)
        sigma = (h_total_rms + a_total_rms) / 2
        mu_shift = (h_total_me + a_total_me) / 2
        teaser_u8 = None
        teaser_u10 = None
        if sigma > 0 and row.total is not None:
            teaser_u8 = round(_normal_cdf((8 - mu_shift) / sigma), 3)
            teaser_u10 = round(_normal_cdf((10 - mu_shift) / sigma), 3)

        # Edge summary bullets
        edge_summary: List[str] = []

        # Variance level
        avg_spread_bucket = (h_spread_bucket + a_spread_bucket) / 2
        if avg_spread_bucket <= 2:
            edge_summary.append("Low spread variance — both teams play close to the number")
        elif avg_spread_bucket >= 4:
            edge_summary.append("High spread variance — outcomes swing wide of the line")

        # Pace direction
        if home_team.pace and away_team.pace:
            avg_pace = (home_team.pace + away_team.pace) / 2
            if avg_pace >= 70:
                edge_summary.append(f"Up-tempo game (avg pace {avg_pace:.0f}) — favors the over")
            elif avg_pace <= 64:
                edge_summary.append(f"Slow-paced game (avg pace {avg_pace:.0f}) — favors the under")

        # Market bias
        if abs(mu_shift) >= 3:
            direction = "over" if mu_shift > 0 else "under"
            edge_summary.append(f"Combined total bias of {mu_shift:+.1f} pts — these teams trend {direction}")

        # Archetype combo
        archetypes = {home_team.archetype, away_team.archetype}
        if "Chaos Team" in archetypes and "Market Follower" in archetypes:
            edge_summary.append("Chaos vs. Follower matchup — high uncertainty, fade the public")
        elif archetypes == {"Market Follower"}:
            edge_summary.append("Both teams are Market Followers — strong teaser candidates")
        elif archetypes == {"Chaos Team"}:
            edge_summary.append("Double Chaos matchup — avoid teasers, expect wild swings")

        # Teaser conclusion (probabilistic)
        if teaser_u10 is not None and teaser_u10 >= 0.90:
            edge_summary.append(f"Teaser +10 lands {teaser_u10*100:.0f}% of the time — strong under teaser play")
        elif teaser_u10 is not None and teaser_u10 >= 0.80:
            edge_summary.append(f"Teaser +10 lands {teaser_u10*100:.0f}% — moderate teaser value")

        # Historical teaser survival insights
        combined_t8 = getattr(row, 'combined_teaser8_rate', None)
        combined_t10 = getattr(row, 'combined_teaser10_rate', None)
        combined_w10 = getattr(row, 'combined_within_10_rate', None)

        if combined_t10 is not None and combined_t10 >= 0.85:
            edge_summary.append(f"Historical +10 survival: {float(combined_t10)*100:.0f}% — both teams stay close")
        elif combined_t10 is not None and combined_t10 < 0.65:
            edge_summary.append(f"Historical +10 survival: {float(combined_t10)*100:.0f}% — blowouts common, avoid teasers")

        if combined_w10 is not None and combined_w10 >= 0.80:
            edge_summary.append(f"Spread stability: {float(combined_w10)*100:.0f}% of games within 10 pts of line")

        # Historical O/U insights
        combined_over = getattr(row, 'combined_over_rate_l10', None)
        combined_under = getattr(row, 'combined_under_rate_l10', None)
        combined_margin = getattr(row, 'combined_avg_total_margin', None)

        if combined_over is not None and combined_over >= 0.65:
            edge_summary.append(f"Over trend: {float(combined_over)*100:.0f}% of L10 games went over — lean over")
        elif combined_under is not None and combined_under >= 0.65:
            edge_summary.append(f"Under trend: {float(combined_under)*100:.0f}% of L10 games went under — lean under")

        if combined_margin is not None and abs(combined_margin) >= 5:
            direction = "over" if combined_margin > 0 else "under"
            edge_summary.append(f"Avg margin vs line: {combined_margin:+.1f} pts — games trend {direction}")

        # Calculate Spread Eagle predictability scores
        spread_predictability = None
        total_predictability = None
        eagle_score = None
        eagle_verdict = "N/A"

        if home_spread_dist and away_spread_dist:
            spread_predictability = round(
                (home_spread_dist.predictability + away_spread_dist.predictability) / 2, 1
            )

        if home_total_dist and away_total_dist:
            total_predictability = round(
                (home_total_dist.predictability + away_total_dist.predictability) / 2, 1
            )

        if spread_predictability is not None and total_predictability is not None:
            eagle_score = round((spread_predictability + total_predictability) / 2, 1)

            # Determine verdict based on Spread Eagle score
            if eagle_score >= 60:
                eagle_verdict = "SPREAD EAGLE"
                edge_summary.insert(0, f"🦅 SPREAD EAGLE ({eagle_score:.0f}) — Elite predictability on both spread & total")
            elif eagle_score >= 50:
                eagle_verdict = "LEAN TEASER"
                edge_summary.insert(0, f"Lean Teaser ({eagle_score:.0f}) — Good predictability, consider for teasers")
            elif eagle_score >= 40:
                eagle_verdict = "CAUTION"
            else:
                eagle_verdict = "AVOID"
                edge_summary.append("Low predictability — avoid teasers on this game")

        games.append(DashboardGame(
            id=row.game_id,
            gameDate=game_date_str,
            gameTime=game_time_str,
            venue=row.venue or "TBD",
            location=row.location or "",
            spread=spread_str,
            total=total_str,
            homeTeam=home_team,
            awayTeam=away_team,
            league="NCAA",
            chaosRating=chaos_rating,
            chaosLabel=chaos_label,
            teaserUnder8Prob=teaser_u8,
            teaserUnder10Prob=teaser_u10,
            edgeSummary=edge_summary,
            combinedTeaser8Rate=float(combined_t8) if combined_t8 is not None else None,
            combinedTeaser10Rate=float(combined_t10) if combined_t10 is not None else None,
            combinedWithin10Rate=float(combined_w10) if combined_w10 is not None else None,
            combinedOverRateL10=float(combined_over) if combined_over is not None else None,
            combinedUnderRateL10=float(combined_under) if combined_under is not None else None,
            combinedAvgTotalMargin=float(combined_margin) if combined_margin is not None else None,
            combinedWithin10TotalRate=float(getattr(row, 'combined_within_10_total_rate', None)) if getattr(row, 'combined_within_10_total_rate', None) is not None else None,
            # Spread Eagle predictability scores
            spreadPredictability=spread_predictability,
            totalPredictability=total_predictability,
            spreadEagleScore=eagle_score,
            spreadEagleVerdict=eagle_verdict,
        ))

    return DashboardResponse(
        date=game_date.isoformat(),
        count=len(games),
        games=games,
    )


# =============================================================================
# MODELS (Pydantic schemas for API responses)
# =============================================================================

class ProbabilityCurvePoint(BaseModel):
    """A single point on the probability curve."""
    threshold: float = Field(..., description="Total points threshold")
    probability: float = Field(..., description="P(Total > threshold)")


class GamePrediction(BaseModel):
    """Full prediction for a single game."""
    game_id: int
    home_team: str
    away_team: str
    game_date: str

    vegas_total: float = Field(..., description="Bovada closing O/U line")
    predicted_mean: float = Field(..., description="Model predicted total")
    predicted_std: float = Field(..., description="Prediction uncertainty (std dev)")

    prob_over_vegas: float = Field(..., description="P(Total > vegas_total)")
    model_edge: float = Field(..., description="predicted_mean - vegas_total")
    confidence: str = Field(..., description="high/medium/low based on edge vs uncertainty")

    probability_curve: List[ProbabilityCurvePoint] = Field(
        ..., description="P(Total > X) for various thresholds"
    )


class PredictionsResponse(BaseModel):
    """Response containing multiple game predictions."""
    generated_at: str
    model_version: str
    count: int
    predictions: List[GamePrediction]


class CustomProbabilityRequest(BaseModel):
    """Request to calculate probability at custom threshold."""
    predicted_mean: float = Field(..., description="Model predicted total")
    predicted_std: float = Field(..., description="Prediction uncertainty")
    threshold: float = Field(..., description="Threshold to calculate P(Total > threshold)")


class CustomProbabilityResponse(BaseModel):
    """Response with calculated probability."""
    threshold: float
    prob_over: float
    prob_under: float


# =============================================================================
# HELPERS
# =============================================================================

PREDICTIONS_FILE = Path("data/predictions/cbb_ou_predictions.json")
MODEL_DIR = Path("models/cbb_ou")


def load_predictions() -> dict:
    """Load cached predictions from JSON file."""
    if not PREDICTIONS_FILE.exists():
        raise HTTPException(
            status_code=503,
            detail="Predictions not yet generated. Run the ML pipeline first."
        )

    with open(PREDICTIONS_FILE, "r") as f:
        return json.load(f)


def calculate_probability_over(
    predicted_mean: float,
    predicted_std: float,
    threshold: float,
) -> float:
    """Calculate P(Total > threshold) using normal distribution."""
    from scipy import stats

    if predicted_std <= 0:
        return 1.0 if predicted_mean > threshold else 0.0

    z_score = (threshold - predicted_mean) / predicted_std
    return float(1 - stats.norm.cdf(z_score))


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(
    "/predictions",
    response_model=PredictionsResponse,
    summary="Get O/U predictions for upcoming games",
)
async def get_predictions(
    min_confidence: Optional[str] = Query(
        None,
        description="Filter by minimum confidence level: low, medium, high"
    ),
    min_edge: Optional[float] = Query(
        None,
        description="Filter by minimum absolute model edge (points)"
    ),
    limit: int = Query(50, ge=1, le=200, description="Maximum games to return"),
):
    """
    Get Over/Under predictions for upcoming college basketball games.

    Returns probability distributions for each game including:
    - Model predicted total and uncertainty
    - P(Over) at the Vegas line
    - Full probability curve for various thresholds
    - Confidence level based on edge vs uncertainty

    Example probability curve output:
    ```
    130 points - 92% probability of going over
    145 points - 75%
    150 points - 65%
    155 points - 50% (Vegas line)
    165 points - 30%
    175 points - 15%
    ```
    """
    data = load_predictions()

    predictions = data.get("predictions", [])

    # Apply filters
    if min_confidence:
        confidence_order = {"low": 0, "medium": 1, "high": 2}
        min_level = confidence_order.get(min_confidence.lower(), 0)
        predictions = [
            p for p in predictions
            if confidence_order.get(p.get("confidence", "low"), 0) >= min_level
        ]

    if min_edge is not None:
        predictions = [
            p for p in predictions
            if abs(p.get("model_edge", 0)) >= min_edge
        ]

    # Sort by absolute edge (strongest predictions first)
    predictions.sort(key=lambda p: abs(p.get("model_edge", 0)), reverse=True)

    # Limit results
    predictions = predictions[:limit]

    # Transform to response format
    formatted_predictions = []
    for p in predictions:
        curve = [
            ProbabilityCurvePoint(threshold=float(k), probability=v)
            for k, v in sorted(p.get("probability_curve", {}).items(), key=lambda x: float(x[0]))
        ]
        formatted_predictions.append(
            GamePrediction(
                game_id=p["game_id"],
                home_team=p["home_team"],
                away_team=p["away_team"],
                game_date=p["game_date"],
                vegas_total=p["vegas_total"],
                predicted_mean=p["predicted_mean"],
                predicted_std=p["predicted_std"],
                prob_over_vegas=p["prob_over_vegas"],
                model_edge=p["model_edge"],
                confidence=p["confidence"],
                probability_curve=curve,
            )
        )

    return PredictionsResponse(
        generated_at=data.get("generated_at", ""),
        model_version=data.get("model_version", "unknown"),
        count=len(formatted_predictions),
        predictions=formatted_predictions,
    )


@router.get(
    "/predictions/{game_id}",
    response_model=GamePrediction,
    summary="Get prediction for a specific game",
)
async def get_prediction_by_id(game_id: int):
    """Get the O/U prediction for a specific game by ID."""
    data = load_predictions()

    for p in data.get("predictions", []):
        if p["game_id"] == game_id:
            curve = [
                ProbabilityCurvePoint(threshold=float(k), probability=v)
                for k, v in sorted(p.get("probability_curve", {}).items(), key=lambda x: float(x[0]))
            ]
            return GamePrediction(
                game_id=p["game_id"],
                home_team=p["home_team"],
                away_team=p["away_team"],
                game_date=p["game_date"],
                vegas_total=p["vegas_total"],
                predicted_mean=p["predicted_mean"],
                predicted_std=p["predicted_std"],
                prob_over_vegas=p["prob_over_vegas"],
                model_edge=p["model_edge"],
                confidence=p["confidence"],
                probability_curve=curve,
            )

    raise HTTPException(status_code=404, detail=f"Game {game_id} not found in predictions")


@router.post(
    "/probability",
    response_model=CustomProbabilityResponse,
    summary="Calculate probability at custom threshold",
)
async def calculate_custom_probability(request: CustomProbabilityRequest):
    """
    Calculate P(Total > threshold) for a custom threshold.

    Useful for:
    - Evaluating alternate lines
    - Calculating probability at user-specified totals
    - Building custom betting strategies

    Example:
        Given predicted_mean=155, predicted_std=12, threshold=160
        Returns: prob_over=0.338, prob_under=0.662
    """
    prob_over = calculate_probability_over(
        request.predicted_mean,
        request.predicted_std,
        request.threshold,
    )

    return CustomProbabilityResponse(
        threshold=request.threshold,
        prob_over=round(prob_over, 4),
        prob_under=round(1 - prob_over, 4),
    )


@router.get("/health", summary="Health check for CBB model")
async def cbb_health():
    """Check if model artifacts and predictions are available."""
    model_exists = (MODEL_DIR / "model.joblib").exists()
    predictions_exist = PREDICTIONS_FILE.exists()

    status = "healthy" if (model_exists and predictions_exist) else "degraded"

    return {
        "status": status,
        "model_loaded": model_exists,
        "predictions_available": predictions_exist,
    }


# =============================================================================
# TEAM DISTRIBUTION MODELS (for KDE visualization)
# =============================================================================

class TeamDistributionStats(BaseModel):
    """Distribution statistics for a single team."""
    team_id: int
    team_name: str
    games: int
    mean: float
    median: float
    std: float
    iqr: float
    p5: float
    p25: float
    p75: float
    p95: float
    min_val: float
    max_val: float
    within_8_rate: float
    within_10_rate: float
    skewness: float
    predictability: float
    margins: List[float]  # Raw margins for frontend KDE calculation


class GameDistributionResponse(BaseModel):
    """Distribution data for both teams in a game matchup."""
    game_id: int
    game_date: str
    home_team: str
    away_team: str
    spread: Optional[float]
    total: Optional[float]

    # Home team distributions
    home_spread_dist: Optional[TeamDistributionStats]
    home_total_dist: Optional[TeamDistributionStats]

    # Away team distributions
    away_spread_dist: Optional[TeamDistributionStats]
    away_total_dist: Optional[TeamDistributionStats]

    # Combined game predictability
    combined_spread_predictability: Optional[float]
    combined_total_predictability: Optional[float]
    spread_eagle_score: Optional[float]

    # Verdict
    verdict: str  # "SPREAD EAGLE", "LEAN TEASER", "CAUTION", "AVOID"


@router.get(
    "/distribution/{game_id}",
    response_model=GameDistributionResponse,
    summary="Get margin distributions for KDE visualization",
)
async def get_game_distributions(
    game_id: int,
    date: str = Query(
        ...,
        description="Date in YYYY-MM-DD format",
        examples=["2026-01-31"],
    ),
    db: Session = Depends(get_db),
):
    """
    Get margin distribution data for both teams in a matchup.

    Returns raw margin arrays and distribution statistics for:
    - Spread (cover_margin) distributions
    - Total (total_margin) distributions

    Used by frontend for KDE (kernel density estimation) graphs
    that visualize how predictable each team is.
    """
    try:
        game_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Get game info
    game_query = text("""
        SELECT
            game_id, game_date, home_team, away_team, home_team_id, away_team_id,
            spread, total
        FROM marts_cbb.fct_cbb__game_dashboard
        WHERE game_id = :game_id AND DATE(game_date) = :game_date
        LIMIT 1
    """)

    game_result = db.execute(game_query, {"game_id": game_id, "game_date": game_date}).fetchone()

    if not game_result:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get distribution stats for each team (try new table first, fallback to raw query)
    def get_team_distribution(team_id: int, margin_type: str) -> Optional[TeamDistributionStats]:
        """Get distribution for a team from raw data."""
        if margin_type == "spread":
            table = "intermediate_cbb.int_cbb__team_spread_volatility"
            margin_col = "cover_margin"
        else:
            table = "intermediate_cbb.int_cbb__team_ou_trends"
            margin_col = "total_margin"

        query = text(f"""
            SELECT
                team_id,
                team_name,
                {margin_col} as margin
            FROM {table}
            WHERE team_id = :team_id
              AND season = 2026
              AND {margin_col} IS NOT NULL
            ORDER BY game_date
        """)

        result = db.execute(query, {"team_id": team_id}).fetchall()

        if len(result) < 5:
            return None

        margins = [float(r.margin) for r in result]
        team_name = result[0].team_name

        # Calculate stats (using module-level numpy import)
        margins_arr = np.array(margins)

        mean = float(np.mean(margins_arr))
        median = float(np.median(margins_arr))
        std = float(np.std(margins_arr))
        p5, p25, p75, p95 = [float(np.percentile(margins_arr, p)) for p in [5, 25, 75, 95]]
        iqr = p75 - p25

        within_8 = float(np.mean(np.abs(margins_arr) < 8))
        within_10 = float(np.mean(np.abs(margins_arr) < 10))

        # Skewness approximation
        skewness = 3 * (mean - median) / std if std > 0 else 0

        # Predictability score
        std_score = max(0, min(100, 100 - (std - 5) * (100 / 15)))
        iqr_score = max(0, min(100, 50 - iqr * 2))
        w10_score = within_10 * 100
        predictability = std_score * 0.3 + iqr_score * 0.2 + w10_score * 0.5

        return TeamDistributionStats(
            team_id=team_id,
            team_name=team_name,
            games=len(margins),
            mean=round(mean, 2),
            median=round(median, 2),
            std=round(std, 2),
            iqr=round(iqr, 2),
            p5=round(p5, 2),
            p25=round(p25, 2),
            p75=round(p75, 2),
            p95=round(p95, 2),
            min_val=round(float(np.min(margins_arr)), 2),
            max_val=round(float(np.max(margins_arr)), 2),
            within_8_rate=round(within_8, 3),
            within_10_rate=round(within_10, 3),
            skewness=round(skewness, 3),
            predictability=round(predictability, 1),
            margins=margins
        )

    # Get distributions for both teams
    home_spread = get_team_distribution(game_result.home_team_id, "spread")
    home_total = get_team_distribution(game_result.home_team_id, "total")
    away_spread = get_team_distribution(game_result.away_team_id, "spread")
    away_total = get_team_distribution(game_result.away_team_id, "total")

    # Calculate combined scores
    combined_spread = None
    combined_total = None
    eagle_score = None

    if home_spread and away_spread:
        combined_spread = (home_spread.predictability + away_spread.predictability) / 2

    if home_total and away_total:
        combined_total = (home_total.predictability + away_total.predictability) / 2

    if combined_spread and combined_total:
        eagle_score = (combined_spread + combined_total) / 2

    # Determine verdict
    if eagle_score and eagle_score >= 60:
        verdict = "SPREAD EAGLE"
    elif eagle_score and eagle_score >= 50:
        verdict = "LEAN TEASER"
    elif eagle_score and eagle_score >= 40:
        verdict = "CAUTION"
    else:
        verdict = "AVOID"

    return GameDistributionResponse(
        game_id=game_id,
        game_date=str(game_date),
        home_team=game_result.home_team,
        away_team=game_result.away_team,
        spread=float(game_result.spread) if game_result.spread else None,
        total=float(game_result.total) if game_result.total else None,
        home_spread_dist=home_spread,
        home_total_dist=home_total,
        away_spread_dist=away_spread,
        away_total_dist=away_total,
        combined_spread_predictability=round(combined_spread, 1) if combined_spread else None,
        combined_total_predictability=round(combined_total, 1) if combined_total else None,
        spread_eagle_score=round(eagle_score, 1) if eagle_score else None,
        verdict=verdict
    )
