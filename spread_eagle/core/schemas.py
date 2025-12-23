
from pydantic import BaseModel

class GameInput(BaseModel):
    sport: str
    home_team: str
    away_team: str
    game_datetime: str | None = None

class PredictionOutput(BaseModel):
    sport: str
    home_team: str
    away_team: str
    predicted_total: float | None = None
    predicted_spread: float | None = None
    confidence: float | None = None
    tl_dr: str
