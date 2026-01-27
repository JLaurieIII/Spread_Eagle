"""
================================================================================
CBB API Router
================================================================================

Endpoints for serving college basketball games and predictions.

Endpoints:
    GET /cbb/games              - Get games for a specific date
    GET /cbb/dashboard          - Get full game cards for dashboard UI
    GET /cbb/predictions        - Get predictions for upcoming games
    GET /cbb/predictions/{id}   - Get prediction for specific game
    GET /cbb/probability        - Calculate P(Total > X) for custom threshold

================================================================================
"""

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
import json
import joblib

from spread_eagle.core.database import get_db

router = APIRouter(prefix="/cbb", tags=["College Basketball"])


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
        example="2026-01-15",
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
            g.away_team_id,
            g.away_team,
            g.away_conference,
            g.away_points,
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
                short=_get_short_name(row.home_team),
                record=row.home_record,
                conference=row.home_conference,
                ats_record=home_ats if home_ats and home_ats != "0-0-0" else None,
                ou_record=home_ou if home_ou and home_ou != "0-0-0" else None,
            ),
            away=TeamInfo(
                name=row.away_team or "TBD",
                short=_get_short_name(row.away_team),
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
    result: str  # "W" or "L"
    score: str
    spreadResult: float


class DashboardTeamData(BaseModel):
    """Complete team data for dashboard card."""
    name: str
    shortName: str
    primaryColor: str
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


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Get full game cards for dashboard UI",
)
async def get_dashboard_games(
    date: str = Query(
        ...,
        description="Date in YYYY-MM-DD format",
        example="2026-01-24",
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
            game_timestamp,
            venue,
            location,

            -- Home team
            home_team,
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
            total

        FROM marts_cbb.fct_cbb__game_dashboard
        WHERE DATE(game_date) = :game_date
        ORDER BY game_timestamp, game_id
    """)

    result = db.execute(query, {"game_date": game_date})
    rows = result.fetchall()

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
                    result=g.get("result", ""),
                    score=score,
                    spreadResult=float(g.get("spread_result", 0) or 0),
                ))
            return results
        except (json.JSONDecodeError, TypeError):
            return []

    games = []
    for row in rows:
        # Parse start time
        if row.game_timestamp:
            start_dt = row.game_timestamp
            game_date_str = _format_game_date(start_dt)
            game_time_str = _format_game_time(start_dt)
        elif row.game_date:
            game_date_str = _format_game_date(datetime.combine(row.game_date, datetime.min.time()))
            game_time_str = "TBD"
        else:
            game_date_str = "TBD"
            game_time_str = "TBD"

        # Format spread string
        spread_str = None
        if row.spread is not None:
            spread_val = float(row.spread)
            if spread_val < 0:
                spread_str = f"{_get_short_name(row.home_team)} {spread_val}"
            elif spread_val > 0:
                spread_str = f"{_get_short_name(row.away_team)} -{abs(spread_val)}"
            else:
                spread_str = "PICK"

        # Format total
        total_str = str(row.total) if row.total else None

        # Build home team data (records are already formatted as strings like "12-5")
        home_team = DashboardTeamData(
            name=row.home_team or "TBD",
            shortName=_get_short_name(row.home_team),
            primaryColor=_get_team_color(row.home_team),
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
        )

        # Build away team data
        away_team = DashboardTeamData(
            name=row.away_team or "TBD",
            shortName=_get_short_name(row.away_team),
            primaryColor=_get_team_color(row.away_team),
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
        )

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
