import requests
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
from spread_eagle.core.database import SessionLocal, engine
from spread_eagle.core.models import Base, Team, Game
from spread_eagle.config.settings import settings
import time

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

BASE_URL = "https://api.collegefootballdata.com"

def get_headers():
    if not settings.CFB_API_KEY:
        raise ValueError("CFB_API_KEY is not set in environment variables.")
    return {
        "Authorization": f"Bearer {settings.CFB_API_KEY}",
        "Accept": "application/json"
    }

def fetch_teams():
    print("Fetching Teams via raw Request...")
    url = f"{BASE_URL}/teams"
    resp = requests.get(url, headers=get_headers(), timeout=30)
    if resp.status_code != 200:
        print(f"Error fetching teams: {resp.status_code} {resp.text}")
        return []
    return resp.json()

def ingest_teams(db: Session):
    teams_data = fetch_teams()
    print(f"Found {len(teams_data)} teams. Ingesting...")
    
    count = 0
    for t in teams_data:
        # Check if team exists
        t_id = t.get('id')
        if not t_id:
            continue
            
        existing_team = db.query(Team).filter(Team.id == t_id).first()
        if not existing_team:
            new_team = Team(
                id=t_id,
                school=t.get('school'),
                mascot=t.get('mascot'),
                abbreviation=t.get('abbreviation'),
                conference=t.get('conference'),
                division=t.get('division'),
                color=t.get('color'),
                alt_color=t.get('alt_color'),
                logos=str(t.get('logos')) if t.get('logos') else None,
                raw_data=t
            )
            db.add(new_team)
            count += 1
    db.commit()
    print(f"Teams ingested: {count} new teaams added.")

def fetch_games_raw(year: int, season_type: str = "regular"):
    url = f"{BASE_URL}/games"
    params = {
        "year": year,
        "seasonType": season_type
    }
    resp = requests.get(url, headers=get_headers(), params=params, timeout=30)
    if resp.status_code != 200:
        print(f"Error fetching games for {year}: {resp.status_code}")
        return []
    return resp.json()

def ingest_games(db: Session, year: int):
    print(f"Ingesting Games for {year}...")
    
    # Fetch Regular Season and Postseason
    regular = fetch_games_raw(year, "regular")
    post = fetch_games_raw(year, "postseason")
    all_games = regular + post
    
    print(f"Fetched {len(all_games)} games for {year}.")
    
    count = 0
    for g in all_games:
        g_id = g.get('id')
        if not g_id:
            continue
            
        existing_game = db.query(Game).filter(Game.id == g_id).first()
        if not existing_game:
            # Safe date parsing
            start_date_str = g.get('startDate')
            start_date = None
            if start_date_str:
                try:
                    start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                except ValueError:
                    pass

            new_game = Game(
                id=g_id,
                season=g.get('season'),
                week=g.get('week'),
                season_type=g.get('seasonType'),
                start_date=start_date,
                start_time_tbd=g.get('startTimeTBD'),
                completed=g.get('completed'),
                neutral_site=g.get('neutralSite'),
                conference_game=g.get('conferenceGame'),
                attendance=g.get('attendance'),
                venue_id=g.get('venueId'),
                venue=g.get('venue'),
                home_team_id=g.get('homeId'),
                home_team_score=g.get('homePoints'),
                away_team_id=g.get('awayId'),
                away_team_score=g.get('awayPoints'),
                raw_data=g
            )
            db.add(new_game)
            count += 1
            
    db.commit()
    print(f"Games for {year} ingested: {count} new games.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        # 1. Ingest Teams first (FK requirement)
        ingest_teams(db)
        
        # 2. Ingest Games
        current_year = datetime.now().year
        # User requested 3 years history
        years = range(current_year - 3, current_year + 1)
        for year in years:
             ingest_games(db, year)
             time.sleep(0.5) # Be polite to API
             
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()
