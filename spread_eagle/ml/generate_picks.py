"""
Generate picks for today's unplayed CBB games.
"""
import psycopg2
import pandas as pd
import numpy as np
import joblib
from scipy import stats
from pathlib import Path

# Load model
model_dir = Path("models/cbb_ou")
model = joblib.load(model_dir / "model.joblib")
feature_names = joblib.load(model_dir / "feature_names.joblib")
predicted_std = joblib.load(model_dir / "predicted_std.joblib")

DB_CONFIG = {
    "host": "spread-eagle-db.cbwyw8ky62xm.us-east-2.rds.amazonaws.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "Sport4788!",
}

conn = psycopg2.connect(**DB_CONFIG)

# Get games that haven't been played yet (actual_total = 0)
query = """
    SELECT *
    FROM marts_cbb.fct_cbb__ml_features_ou
    WHERE game_date = '2026-01-10'
      AND actual_total = 0
      AND has_sufficient_history = true
    ORDER BY game_timestamp
"""
df = pd.read_sql(query, conn)
conn.close()

print(f"Found {len(df)} unplayed games for Jan 10 with sufficient history")
print("=" * 90)

if len(df) > 0:
    # Prepare features
    X = df[feature_names].fillna(df[feature_names].median())

    # Get predictions
    predictions = model.predict(X)

    # Calculate probabilities
    results = []
    for idx, (_, row) in enumerate(df.iterrows()):
        pred_mean = predictions[idx]
        vegas = row["vegas_total"]
        edge = pred_mean - vegas

        # P(Over)
        z = (vegas - pred_mean) / predicted_std
        prob_over = 1 - stats.norm.cdf(z)

        # Confidence based on edge/std ratio
        edge_ratio = abs(edge) / predicted_std
        if edge_ratio > 1.5:
            conf = "HIGH"
        elif edge_ratio > 0.5:
            conf = "MEDIUM"
        else:
            conf = "LOW"

        results.append({
            "matchup": f"{row['away_team']} @ {row['home_team']}",
            "vegas": vegas,
            "predicted": round(pred_mean, 1),
            "edge": round(edge, 1),
            "prob_over": round(prob_over * 100, 1),
            "conf": conf,
            "direction": "OVER" if edge > 0 else "UNDER"
        })

    # Sort by absolute edge
    results.sort(key=lambda x: abs(x["edge"]), reverse=True)

    print(f"{'MATCHUP':<40} {'VEGAS':>7} {'PRED':>7} {'EDGE':>7} {'P(O)':>7} {'PICK':>8} {'CONF':>8}")
    print("-" * 90)
    for r in results:
        print(f"{r['matchup']:<40} {r['vegas']:>7.1f} {r['predicted']:>7.1f} {r['edge']:>+7.1f} {r['prob_over']:>6.1f}% {r['direction']:>8} {r['conf']:>8}")

    print("\n" + "=" * 90)
    print("TOP PICKS (Highest Confidence)")
    print("=" * 90)

    # Filter for medium/high confidence
    strong_picks = [r for r in results if r["conf"] in ["HIGH", "MEDIUM"]]

    if strong_picks:
        for r in strong_picks[:10]:
            print(f"\n  {r['matchup']}")
            print(f"    Vegas Total: {r['vegas']}")
            print(f"    Model Predicted: {r['predicted']} ({r['edge']:+.1f} edge)")
            print(f"    P(Over): {r['prob_over']:.1f}%")
            print(f"    >>> PICK: {r['direction']} (Confidence: {r['conf']})")
    else:
        print("\n  No medium/high confidence picks available.")
        print("  All predictions have LOW confidence - model edge is within noise range.")
else:
    print("No unplayed games found")
