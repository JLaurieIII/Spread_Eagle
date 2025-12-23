from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    school = Column(String, index=True) # Not unique, duplicates exist in CFBD
    mascot = Column(String)
    abbreviation = Column(String)
    conference = Column(String)
    division = Column(String)
    color = Column(String)
    alt_color = Column(String)
    logos = Column(Text) # JSON string or URL
    raw_data = Column(JSON) # Store full API response

    # Relationships
    home_games = relationship("Game", foreign_keys="[Game.home_team_id]", back_populates="home_team")
    away_games = relationship("Game", foreign_keys="[Game.away_team_id]", back_populates="away_team")

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True) # ID from the provider (e.g. CFBD ID)
    season = Column(Integer, index=True)
    week = Column(Integer)
    season_type = Column(String) # regular, postseason
    start_date = Column(DateTime)
    start_time_tbd = Column(Boolean, default=False)
    completed = Column(Boolean, default=False)
    neutral_site = Column(Boolean, default=False)
    conference_game = Column(Boolean, default=False)
    attendance = Column(Integer)
    venue_id = Column(Integer)
    venue = Column(String)
    raw_data = Column(JSON) # Store full API response
    
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    home_team_score = Column(Integer)
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_score = Column(Integer)

    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")
    betting_lines = relationship("BettingLine", back_populates="game")
    game_events = relationship("GameEvent", back_populates="game")
    predictions = relationship("Prediction", back_populates="game")

class BettingLine(Base):
    __tablename__ = "betting_lines"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    provider = Column(String) # e.g. "Bovada", "Consensus"
    spread = Column(Float)
    spread_open = Column(Float)
    over_under = Column(Float)
    over_under_open = Column(Float)
    moneyline_home = Column(Integer)
    moneyline_away = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="betting_lines")

class GameEvent(Base):
    """
    Qualitative events that affect the game:
    - Opt-outs
    - Coaching changes
    - Significant Injuries
    """
    __tablename__ = "game_events"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    event_type = Column(String, index=True) # "opt_out", "injury", "coaching_change"
    description = Column(String)
    severity = Column(Float) # 0.0 to 1.0 impact score
    player_name = Column(String, nullable=True)
    position = Column(String, nullable=True)
    
    game = relationship("Game", back_populates="game_events")

class Prediction(Base):
    """
    Outputs from 'The Thought Process'
    """
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    model_version = Column(String)
    
    predicted_spread = Column(Float)
    predicted_total = Column(Float)
    confidence_score = Column(Float) # 0.0 to 1.0 using the qualitative factors
    
    insights = Column(Text) # JSON or text summary of WHY (e.g. "Star QB out -> Spread adjusting +3")
    
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="predictions")
