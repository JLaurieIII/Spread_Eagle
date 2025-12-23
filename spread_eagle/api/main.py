from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from spread_eagle.core.database import get_db, engine, Base
from spread_eagle.core.models import Game
from spread_eagle.core.brain import SpreadEagleBrain
from pydantic import BaseModel, ConfigDict
from datetime import datetime

# Initialize Tables (if not already)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Spread Eagle API", description="AI-Driven College Football Insights")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production replace with frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Schemas ---
class GameResponse(BaseModel):
    id: int
    home_team_id: int
    home_team_score: Optional[int]
    away_team_id: int
    away_team_score: Optional[int]
    season: int
    week: int
    start_date: Optional[datetime]
    venue: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class PredictionResponse(BaseModel):
    game_id: int
    predicted_spread: float
    raw_model_prediction: float
    qualitative_adjustment: float
    insights: List[str]

# --- Endpoints ---

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/games", response_model=List[GameResponse])
def get_games(season: int = 2024, week: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Game).filter(Game.season == season)
    if week:
        query = query.filter(Game.week == week)
    return query.all()

@app.get("/predict/{game_id}", response_model=PredictionResponse)
def get_prediction(game_id: int, db: Session = Depends(get_db)):
    brain = SpreadEagleBrain(db)
    
    # Try to predict
    try:
        if not brain.model:
            brain.load_model()
            
        prediction = brain.predict(game_id)
        if not prediction:
             raise HTTPException(status_code=404, detail="Game not found or prediction failed")
             
        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("spread_eagle.api.main:app", host="0.0.0.0", port=8000, reload=True)
