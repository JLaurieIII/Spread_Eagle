import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from spread_eagle.core.models import Game, Team, GameEvent, Prediction
from datetime import datetime
import pickle
import os

class SpreadEagleBrain:
    def __init__(self, db: Session):
        self.db = db
        self.model = None
        self.model_path = "spread_eagle_model.pkl"

    def load_data(self):
        """
        Fetch completed games from DB and convert to DataFrame for training
        """
        games = self.db.query(Game).filter(Game.completed == True).all()
        data = []
        for g in games:
            if g.home_team_score is not None and g.away_team_score is not None:
                data.append({
                    "game_id": g.id,
                    "season": g.season,
                    "week": g.week,
                    "home_team_id": g.home_team_id,
                    "away_team_id": g.away_team_id,
                    "home_score": g.home_team_score,
                    "away_score": g.away_team_score,
                    "actual_spread": g.away_team_score - g.home_team_score # Negative means Home won by X
                })
        return pd.DataFrame(data)

    def engineer_features(self, df):
        """
        Calculate rolling averages for teams to use as features.
        Trying to predict game N using stats from games 1..N-1
        """
        # This is a simplified feature engineering for the prototype
        # Ideally we want pre-game stats. 
        # For now, we'll compute global averages per team per season as a proxy or simple rolling average
        
        # Sort by date (sequence)
        df = df.sort_values(by=['season', 'week'])
        
        # We need to build a "stats so far" dictionary
        team_stats = {} # team_id -> {points_scored: [], points_allowed: []}
        
        features = []
        
        for index, row in df.iterrows():
            h_id = row['home_team_id']
            a_id = row['away_team_id']
            
            # Get stats for home team so far
            h_stats = team_stats.get(h_id, {'scored': [], 'allowed': []})
            a_stats = team_stats.get(a_id, {'scored': [], 'allowed': []})
            
            # Simple features: Avg Score Last 5 Games
            h_avg_score = np.mean(h_stats['scored'][-5:]) if h_stats['scored'] else 25.0
            h_avg_allowed = np.mean(h_stats['allowed'][-5:]) if h_stats['allowed'] else 25.0
            
            a_avg_score = np.mean(a_stats['scored'][-5:]) if a_stats['scored'] else 25.0
            a_avg_allowed = np.mean(a_stats['allowed'][-5:]) if a_stats['allowed'] else 25.0
            
            features.append({
                "game_id": row['game_id'],
                "home_avg_score": h_avg_score,
                "home_avg_allowed": h_avg_allowed,
                "away_avg_score": a_avg_score,
                "away_avg_allowed": a_avg_allowed,
                "target_spread": row['actual_spread']
            })
            
            # Update stats
            h_stats['scored'].append(row['home_score'])
            h_stats['allowed'].append(row['away_score'])
            team_stats[h_id] = h_stats
            
            a_stats['scored'].append(row['away_score'])
            a_stats['allowed'].append(row['home_score'])
            team_stats[a_id] = a_stats
            
        return pd.DataFrame(features)

    def train(self):
        print("Loading data...")
        raw_df = self.load_data()
        if raw_df.empty:
            print("No data found to train on.")
            return
            
        print(f"Engineering features for {len(raw_df)} games...")
        train_df = self.engineer_features(raw_df)
        
        X = train_df[["home_avg_score", "home_avg_allowed", "away_avg_score", "away_avg_allowed"]]
        y = train_df["target_spread"]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        print("Training Random Forest...")
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        
        # Eval
        predictions = self.model.predict(X_test)
        mae = mean_absolute_error(y_test, predictions)
        print(f"Model MAE: {mae:.2f} points")
        
        # Save
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        print("Model saved.")

    def load_model(self):
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            return True
        return False

    def predict(self, game_id: int):
        if not self.model:
            if not self.load_model():
                raise ValueError("Model not trained or found.")
                
        # Get game info
        game = self.db.query(Game).filter(Game.id == game_id).first()
        if not game:
            return None
            
        # We need "current" stats for home/away teams
        # This is expensive to compute on fly if we don't cache stats, 
        # but for prototype we can just re-run engineer_features on all history + this game 
        # OR just query the last 5 games for each team from DB directly.
        # Let's do the latter for efficiency.
        
        home_games = self.db.query(Game).filter((Game.home_team_id == game.home_team_id) | (Game.away_team_id == game.home_team_id)).filter(Game.completed == True).order_by(Game.start_date.desc()).limit(5).all()
        away_games = self.db.query(Game).filter((Game.home_team_id == game.away_team_id) | (Game.away_team_id == game.away_team_id)).filter(Game.completed == True).order_by(Game.start_date.desc()).limit(5).all()
        
        def get_avgs(team_id, games_list):
            scores = []
            allowed = []
            for g in games_list:
                if g.home_team_id == team_id:
                    scores.append(g.home_team_score)
                    allowed.append(g.away_team_score)
                else:
                    scores.append(g.away_team_score)
                    allowed.append(g.home_team_score)
            return np.mean(scores) if scores else 25.0, np.mean(allowed) if allowed else 25.0
            
        h_avg_s, h_avg_a = get_avgs(game.home_team_id, home_games)
        a_avg_s, a_avg_a = get_avgs(game.away_team_id, away_games)
        
        # Inference
        X_input = pd.DataFrame([{
            "home_avg_score": h_avg_s,
            "home_avg_allowed": h_avg_a,
            "away_avg_score": a_avg_s,
            "away_avg_allowed": a_avg_a
        }])
        
        predicted_spread = self.model.predict(X_input)[0]
        
        # --- THE THOUGHT PROCESS (Qualitative Adjustment) ---
        adjustment = 0.0
        insights = []
        
        # Check for events
        events = self.db.query(GameEvent).filter(GameEvent.game_id == game_id).all()
        for event in events:
            # Simple heuristic logic
            impact = 0
            if event.event_type == "opt_out":
                # If key player out, team performs worse.
                # If home team event -> home score decreases (spread (away - home) increases)
                # If away team event -> away score decreases (spread decreases)
                severity = event.severity or 3.0 # Default 3 points
                if event.team_id == game.home_team_id:
                    impact = severity # Spread (Away - Home) gets more positive (Away wins by more)
                    insights.append(f"Home team Opt-Out ({event.player_name}): Adjusting spread by +{severity}")
                else:
                    impact = -severity
                    insights.append(f"Away team Opt-Out ({event.player_name}): Adjusting spread by -{severity}")
            
            elif event.event_type == "coaching_change":
                # Chaos factor
                severity = event.severity or 2.0
                # Usually negative for the team
                if event.team_id == game.home_team_id:
                    impact = severity
                    insights.append(f"Home Coaching Change: Adjusting spread by +{severity}")
                else:
                    impact = -severity
                    insights.append(f"Away Coaching Change: Adjusting spread by -{severity}")
            
            adjustment += impact

        final_prediction = predicted_spread + adjustment
        
        return {
            "game_id": game_id,
            "predicted_spread": final_prediction,
            "raw_model_prediction": predicted_spread,
            "qualitative_adjustment": adjustment,
            "insights": insights
        }
