"""
Teaser Win Prediction Model

Trains an XGBoost classifier to predict win_teased_8 using
variance/behavior features from the dbt pipeline.

Key design decisions:
- Chronological train/test split (no future leakage)
- Only use games with sufficient history (10+ prior games)
- Features are all computed from prior games only
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import psycopg2
import warnings
warnings.filterwarnings('ignore')


def load_data():
    """Load the teaser dataset from PostgreSQL."""
    print("Loading data from PostgreSQL...")

    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='spread_eagle',
        user='dbeaver_user',
        password='Sport4788!'
    )

    query = """
    SELECT *
    FROM dbt_dev.fct_cbb_teaser_spread_dataset
    WHERE win_teased_8 IS NOT NULL
      AND has_sufficient_history = true
    ORDER BY game_date, game_id
    """

    df = pd.read_sql(query, conn)
    conn.close()

    print(f"Loaded {len(df):,} rows")
    return df


def prepare_features(df):
    """Select and prepare features for training."""

    # Define feature columns (all computed from prior games)
    feature_cols = [
        # Spread behavior features
        'mean_cover_margin_last3', 'stddev_cover_margin_last3',
        'mean_cover_margin_last5', 'stddev_cover_margin_last5',
        'mean_cover_margin_last10', 'stddev_cover_margin_last10',
        'mean_cover_margin_last20', 'stddev_cover_margin_last20',
        'within_7_rate_last5', 'within_10_rate_last5',
        'within_7_rate_last10', 'within_10_rate_last10',
        'downside_tail_rate_last5', 'downside_tail_rate_last10',

        # Total behavior features
        'mean_total_error_last5', 'stddev_total_error_last5',
        'mean_total_error_last10', 'stddev_total_error_last10',
        'within_8_total_rate_last10', 'within_10_total_rate_last10',
        'over_rate_last10',

        # Trend features
        'ats_win_rate_last3', 'ats_win_rate_last5',
        'ats_win_rate_last10', 'ats_win_rate_last20',
        'ats_streak',
        'spread_variance_contraction_3v10', 'spread_variance_contraction_5v20',

        # Market profile
        'mean_spread_faced_last10', 'stddev_spread_faced_last10',
        'favorite_rate_last10',
        'spread_consistency_last10',

        # Tail risk
        'downside_tail_8_rate_last10', 'downside_tail_10_rate_last10',
        'downside_tail_15_rate_last10',
        'teaser_8_survival_last10', 'teaser_8_survival_last20',
        'blowout_rate_last10',
        'worst_cover_margin_last10',
        'tail_asymmetry_10_last10',

        # Game context (known at bet time)
        'closing_spread_team', 'closing_total',
        'spread_movement', 'total_movement',
    ]

    # Filter to columns that exist
    available_cols = [c for c in feature_cols if c in df.columns]
    missing_cols = [c for c in feature_cols if c not in df.columns]

    if missing_cols:
        print(f"Warning: {len(missing_cols)} features not found: {missing_cols[:5]}...")

    print(f"Using {len(available_cols)} features")

    X = df[available_cols].copy()
    y = df['win_teased_8'].astype(int)

    # Add is_home as binary feature
    if 'is_home' in df.columns:
        X['is_home'] = df['is_home'].astype(int)

    return X, y, df


def chronological_split(X, y, df, test_size=0.2):
    """Split data chronologically to prevent future leakage."""

    # Sort by date (already sorted, but ensure)
    sorted_idx = df['game_date'].argsort()
    X = X.iloc[sorted_idx].reset_index(drop=True)
    y = y.iloc[sorted_idx].reset_index(drop=True)
    dates = df['game_date'].iloc[sorted_idx].reset_index(drop=True)

    # Find split point
    split_idx = int(len(X) * (1 - test_size))
    split_date = dates.iloc[split_idx]

    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    print(f"\nChronological Split:")
    print(f"  Train: {len(X_train):,} games (before {split_date})")
    print(f"  Test:  {len(X_test):,} games (from {split_date})")
    print(f"  Train win rate: {y_train.mean():.1%}")
    print(f"  Test win rate:  {y_test.mean():.1%}")

    return X_train, X_test, y_train, y_test


def train_model(X_train, y_train, X_test, y_test):
    """Train XGBoost classifier."""

    print("\nTraining XGBoost model...")

    # Handle missing values
    X_train = X_train.fillna(-999)
    X_test = X_test.fillna(-999)

    # XGBoost parameters tuned for tabular data
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'max_depth': 5,
        'learning_rate': 0.05,
        'n_estimators': 200,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 10,
        'reg_alpha': 0.1,
        'reg_lambda': 1.0,
        'random_state': 42,
        'n_jobs': -1,
    }

    model = xgb.XGBClassifier(**params)

    # Train model
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )

    print(f"  Training complete with {params['n_estimators']} trees")

    return model


def evaluate_model(model, X_train, y_train, X_test, y_test):
    """Evaluate model performance."""

    print("\n" + "=" * 60)
    print("MODEL EVALUATION")
    print("=" * 60)

    # Handle missing values
    X_train = X_train.fillna(-999)
    X_test = X_test.fillna(-999)

    # Predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    y_test_proba = model.predict_proba(X_test)[:, 1]

    # Metrics
    print("\nTest Set Metrics:")
    print(f"  Accuracy:  {accuracy_score(y_test, y_test_pred):.3f}")
    print(f"  Precision: {precision_score(y_test, y_test_pred):.3f}")
    print(f"  Recall:    {recall_score(y_test, y_test_pred):.3f}")
    print(f"  F1 Score:  {f1_score(y_test, y_test_pred):.3f}")
    print(f"  ROC AUC:   {roc_auc_score(y_test, y_test_proba):.3f}")

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_test_pred)
    print(f"\nConfusion Matrix:")
    print(f"  TN: {cm[0,0]:,}  FP: {cm[0,1]:,}")
    print(f"  FN: {cm[1,0]:,}  TP: {cm[1,1]:,}")

    # Compare to baseline (always predict 1)
    baseline_acc = y_test.mean()
    print(f"\nBaseline (always predict win): {baseline_acc:.1%}")
    print(f"Model improvement: {accuracy_score(y_test, y_test_pred) - baseline_acc:+.1%}")

    # Calibration check - bin by predicted probability
    print("\n" + "-" * 60)
    print("CALIBRATION BY PREDICTED PROBABILITY")
    print("-" * 60)

    df_eval = pd.DataFrame({
        'y_true': y_test.values,
        'y_proba': y_test_proba
    })

    # Create probability bins
    df_eval['prob_bin'] = pd.cut(df_eval['y_proba'],
                                  bins=[0, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 1.0],
                                  labels=['<60%', '60-70%', '70-75%', '75-80%', '80-85%', '85-90%', '>90%'])

    calibration = df_eval.groupby('prob_bin', observed=True).agg({
        'y_true': ['count', 'mean']
    }).round(3)
    calibration.columns = ['count', 'actual_win_rate']
    calibration = calibration[calibration['count'] >= 10]

    print(f"{'Predicted Prob':<15} {'Games':>8} {'Actual Win%':>12}")
    for idx, row in calibration.iterrows():
        print(f"{str(idx):<15} {int(row['count']):>8,} {row['actual_win_rate']:>11.1%}")

    return y_test_proba


def analyze_feature_importance(model, X):
    """Analyze and display feature importance."""

    print("\n" + "=" * 60)
    print("FEATURE IMPORTANCE (Top 20)")
    print("=" * 60)

    importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print(f"{'Feature':<40} {'Importance':>12}")
    print("-" * 52)
    for _, row in importance.head(20).iterrows():
        bar = "#" * int(row['importance'] * 50)
        print(f"{row['feature']:<40} {row['importance']:>10.4f}  {bar}")

    return importance


def backtest_strategy(y_test, y_proba, threshold=0.80):
    """Backtest a simple threshold strategy."""

    print("\n" + "=" * 60)
    print(f"BACKTEST: Bet only when P(win) >= {threshold:.0%}")
    print("=" * 60)

    # Only bet when probability exceeds threshold
    bet_mask = y_proba >= threshold
    n_bets = bet_mask.sum()

    if n_bets == 0:
        print("No bets placed at this threshold")
        return

    wins = y_test.values[bet_mask].sum()
    losses = n_bets - wins
    win_rate = wins / n_bets

    # Assume standard teaser odds (-110)
    # Win: +100/110 = +0.909 units
    # Lose: -1 unit
    profit_per_win = 100 / 110
    profit = wins * profit_per_win - losses
    roi = profit / n_bets

    print(f"  Total games in test: {len(y_test):,}")
    print(f"  Bets placed:         {n_bets:,} ({n_bets/len(y_test):.1%} of games)")
    print(f"  Wins:                {wins:,}")
    print(f"  Losses:              {losses:,}")
    print(f"  Win Rate:            {win_rate:.1%}")
    print(f"  Profit (units):      {profit:+.1f}")
    print(f"  ROI:                 {roi:+.1%}")

    # Compare to betting all games
    all_wins = y_test.sum()
    all_losses = len(y_test) - all_wins
    all_profit = all_wins * profit_per_win - all_losses
    all_roi = all_profit / len(y_test)

    print(f"\n  Comparison (bet all games):")
    print(f"  Win Rate:            {y_test.mean():.1%}")
    print(f"  Profit (units):      {all_profit:+.1f}")
    print(f"  ROI:                 {all_roi:+.1%}")


def main():
    print("=" * 60)
    print("TEASER +8 WIN PREDICTION MODEL")
    print("=" * 60)

    # Load data
    df = load_data()

    # Prepare features
    X, y, df = prepare_features(df)

    # Chronological split
    X_train, X_test, y_train, y_test = chronological_split(X, y, df)

    # Train model
    model = train_model(X_train, y_train, X_test, y_test)

    # Evaluate
    y_proba = evaluate_model(model, X_train, y_train, X_test, y_test)

    # Feature importance
    importance = analyze_feature_importance(model, X)

    # Backtest strategies at different thresholds
    for threshold in [0.80, 0.85, 0.90]:
        backtest_strategy(y_test, y_proba, threshold)

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)

    return model, importance


if __name__ == "__main__":
    model, importance = main()
