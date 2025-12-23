
from fastapi import APIRouter
from spread_eagle.core.schemas import GameInput, PredictionOutput

router = APIRouter(prefix="/cfb")

@router.post("/predict", response_model=PredictionOutput)
def predict(game: GameInput):
    return PredictionOutput(
        sport="cfb",
        home_team=game.home_team,
        away_team=game.away_team,
        tl_dr="Dummy prediction."
    )
