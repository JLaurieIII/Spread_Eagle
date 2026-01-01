"""
Bowl Game Predictions - Spread Eagle ML

This script:
1. Loads historical data from dbt models (completed games)
2. Trains an XGBoost model to predict ATS outcomes
3. Loads upcoming games from fct_cfb__upcoming_predictions
4. Scores today's bowl games with confidence levels

Run: python -m spread_eagle.ml.predict_bowl_games
"""

import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import psycopg2
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score

load_dotenv()


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def load_training_data():
    """Load COMPLETED games for training (has actual outcomes)"""
    conn = get_connection()

    query = """
    SELECT
        game_id, game_date, team_name, opponent_name,
        is_home, spread_close_for_team, total_close,

        team_ats_l5_avg, team_ats_l10_avg,
        team_cover_l5, team_cover_l10,
        team_margin_l5_avg, team_margin_l10_avg,
        team_win_l5, team_win_l10,

        opp_ats_l5_avg, opp_ats_l10_avg,
        opp_cover_l5, opp_cover_l10,
        opp_margin_l5_avg, opp_margin_l10_avg,
        opp_win_l5, opp_win_l10,

        delta_ats_l5, delta_ats_l10,
        delta_cover_l10, delta_margin_l10,

        is_cover, ats_margin

    FROM marts_cfb.fct_cfb__matchup_snapshot
    WHERE team_ats_l10_avg IS NOT NULL
      AND opp_ats_l10_avg IS NOT NULL
      AND is_cover IS NOT NULL
    ORDER BY game_date
    """

    df = pd.read_sql(query, conn)
    conn.close()
    return df


def load_upcoming_games():
    """Load UPCOMING games for prediction (no outcomes yet)"""
    conn = get_connection()

    query = """
    SELECT
        game_id, game_date, team_name, opponent_name,
        is_home, spread_close_for_team, total_close,

        team_ats_l5_avg, team_ats_l10_avg,
        team_cover_l5, team_cover_l10,
        team_margin_l5_avg, team_margin_l10_avg,
        team_win_l5, team_win_l10,

        opp_ats_l5_avg, opp_ats_l10_avg,
        opp_cover_l5, opp_cover_l10,
        opp_margin_l5_avg, opp_margin_l10_avg,
        opp_win_l5, opp_win_l10,

        delta_ats_l5, delta_ats_l10,
        delta_cover_l10, delta_margin_l10

    FROM marts_cfb.fct_cfb__upcoming_predictions
    WHERE team_ats_l10_avg IS NOT NULL
      AND opp_ats_l10_avg IS NOT NULL
    ORDER BY game_date, game_id
    """

    df = pd.read_sql(query, conn)
    conn.close()
    return df


def get_feature_columns():
    return [
        "is_home_int",
        "spread_close_for_team",
        "team_ats_l5_avg",
        "team_ats_l10_avg",
        "team_cover_l5",
        "team_cover_l10",
        "team_margin_l5_avg",
        "team_margin_l10_avg",
        "team_win_l5",
        "team_win_l10",
        "opp_ats_l5_avg",
        "opp_ats_l10_avg",
        "opp_cover_l5",
        "opp_cover_l10",
        "opp_margin_l5_avg",
        "opp_margin_l10_avg",
        "opp_win_l5",
        "opp_win_l10",
        "delta_ats_l5",
        "delta_ats_l10",
        "delta_cover_l10",
        "delta_margin_l10",
    ]


def prepare_features(df):
    df = df.copy()
    df["is_home_int"] = df["is_home"].astype(int)

    for col in get_feature_columns():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def train_model(df):
    """Train XGBoost on historical completed games"""

    df = prepare_features(df)
    feature_cols = get_feature_columns()

    df_clean = df.dropna(subset=feature_cols + ["is_cover"])

    X = df_clean[feature_cols]
    y = df_clean["is_cover"].astype(int)

    # Chronological split
    split_idx = int(len(X) * 0.8)
    X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

    print(f"Training set: {len(X_train):,} games (through ~{df_clean.iloc[split_idx]['game_date']})")
    print(f"Validation set: {len(X_val):,} games")

    model = XGBClassifier(
        n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_val)
    accuracy = accuracy_score(y_val, y_pred)

    print(f"\nValidation Accuracy: {accuracy:.1%}")
    print("(Baseline ~50% - markets are efficient)")

    return model


def predict_games(model, df):
    df = prepare_features(df)
    feature_cols = get_feature_columns()

    df_pred = df.dropna(subset=feature_cols)

    if len(df_pred) == 0:
        print("No games with complete features")
        return df_pred

    X = df_pred[feature_cols]

    probs = model.predict_proba(X)[:, 1]

    df_pred = df_pred.copy()
    df_pred["cover_prob"] = probs
    df_pred["prediction"] = (probs > 0.5).astype(int)
    df_pred["confidence"] = np.abs(probs - 0.5) * 2

    return df_pred


def display_predictions(df):
    print("\n" + "=" * 70)
    print(" SPREAD EAGLE - BOWL GAME PREDICTIONS")
    print("=" * 70)

    for game_date in sorted(df["game_date"].unique()):
        games = df[df["game_date"] == game_date]
        print(f"\n {game_date}")
        print("-" * 70)

        seen = set()
        for _, row in games.iterrows():
            if row["game_id"] in seen:
                continue
            seen.add(row["game_id"])

            if row["is_home"]:
                matchup = f"{row['opponent_name']} @ {row['team_name']}"
                home = row["team_name"]
                spread = row["spread_close_for_team"]
            else:
                matchup = f"{row['team_name']} @ {row['opponent_name']}"
                home = row["opponent_name"]
                spread = -row["spread_close_for_team"]

            prob = row["cover_prob"]
            conf = row["confidence"]

            # Determine pick
            if row["is_home"]:
                pick = row["team_name"] if prob > 0.5 else row["opponent_name"]
                pick_spread = spread if prob > 0.5 else -spread
            else:
                pick = row["team_name"] if prob > 0.5 else row["opponent_name"]
                pick_spread = row["spread_close_for_team"] if prob > 0.5 else -row["spread_close_for_team"]

            edge = "LEAN" if conf < 0.15 else "PLAY" if conf < 0.30 else "STRONG PLAY"
            prob_display = max(prob, 1 - prob)

            print(f"\n  {matchup}")
            print(f"    Line: {home} {spread:+.1f}")
            print(f"    >>> PICK: {pick} {pick_spread:+.1f} ({prob_display:.0%} confidence)")
            print(f"    Rating: {edge}")


def main():
    print("=" * 70)
    print(" SPREAD EAGLE - ML Bowl Game Predictor")
    print(" Powered by XGBoost + dbt Analytics")
    print("=" * 70)

    print("\n[1] Loading training data (completed games)...")
    train_df = load_training_data()
    print(f"    Loaded {len(train_df):,} historical games")

    print("\n[2] Training XGBoost model...")
    model = train_model(train_df)

    print("\n[3] Loading upcoming games...")
    upcoming_df = load_upcoming_games()
    print(f"    Found {len(upcoming_df) // 2} upcoming games with lines")

    if len(upcoming_df) == 0:
        print("\n    No upcoming games found! Run dbt to rebuild models.")
        return

    print("\n[4] Generating predictions...")
    predictions = predict_games(model, upcoming_df)

    display_predictions(predictions)

    print("\n" + "=" * 70)
    print(" TOP FEATURES (Model Weights)")
    print("=" * 70)
    for feat, imp in sorted(
        zip(get_feature_columns(), model.feature_importances_), key=lambda x: -x[1]
    )[:8]:
        bar = "#" * int(imp * 50)
        print(f"  {feat:25} {bar} {imp:.3f}")

    print("\n" + "=" * 70)
    print(" Good luck! Bet responsibly.")
    print("=" * 70)


if __name__ == "__main__":
    main()
