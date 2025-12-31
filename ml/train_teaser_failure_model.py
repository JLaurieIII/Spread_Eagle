"""
Teaser FAILURE Prediction Model

Instead of predicting wins (76.8% baseline), we predict FAILURES.
Goal: Identify the ~23% of games to AVOID.

Key insight: It's easier to find patterns in blowouts than in close wins.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, average_precision_score
)
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

    feature_cols = [
        # Spread behavior - key for failures
        'mean_cover_margin_last3', 'stddev_cover_margin_last3',
        'mean_cover_margin_last5', 'stddev_cover_margin_last5',
        'mean_cover_margin_last10', 'stddev_cover_margin_last10',
        'mean_cover_margin_last20', 'stddev_cover_margin_last20',
        'mean_abs_cover_margin_last5', 'mean_abs_cover_margin_last10',
        'within_7_rate_last5', 'within_10_rate_last5',
        'within_7_rate_last10', 'within_10_rate_last10',
        'within_7_rate_last20', 'within_10_rate_last20',
        'downside_tail_rate_last5', 'downside_tail_rate_last10',
        'downside_tail_rate_last20',

        # Total behavior
        'mean_total_error_last5', 'stddev_total_error_last5',
        'mean_total_error_last10', 'stddev_total_error_last10',
        'mean_abs_total_error_last5', 'mean_abs_total_error_last10',
        'within_8_total_rate_last10', 'within_10_total_rate_last10',
        'over_rate_last5', 'over_rate_last10',

        # Trend features
        'ats_win_rate_last3', 'ats_win_rate_last5',
        'ats_win_rate_last10', 'ats_win_rate_last20',
        'ats_streak',
        'spread_variance_contraction_3v10', 'spread_variance_contraction_5v20',
        'total_variance_contraction_3v10',

        # Market profile
        'mean_spread_faced_last10', 'stddev_spread_faced_last10',
        'favorite_rate_last10', 'favorite_rate_last20',
        'mean_total_faced_last10',
        'spread_consistency_last10', 'spread_consistency_last20',

        # Tail risk - CRITICAL for failure prediction
        'downside_tail_8_rate_last5', 'downside_tail_8_rate_last10',
        'downside_tail_10_rate_last5', 'downside_tail_10_rate_last10',
        'downside_tail_12_rate_last10', 'downside_tail_15_rate_last10',
        'downside_tail_8_rate_last20', 'downside_tail_10_rate_last20',
        'downside_tail_15_rate_last20', 'downside_tail_20_rate_last20',
        'teaser_8_survival_last10', 'teaser_8_survival_last20',
        'teaser_10_survival_last10', 'teaser_10_survival_last20',
        'blowout_rate_last5', 'blowout_rate_last10', 'blowout_rate_last20',
        'worst_cover_margin_last10', 'worst_cover_margin_last20',
        'tail_asymmetry_10_last10', 'tail_asymmetry_15_last20',

        # Game context
        'closing_spread_team', 'closing_total',
        'spread_movement', 'total_movement',
    ]

    available_cols = [c for c in feature_cols if c in df.columns]
    print(f"Using {len(available_cols)} features")

    X = df[available_cols].copy()

    # TARGET: Predict FAILURE (1 = teaser failed, 0 = teaser won)
    y = (df['win_teased_8'] == 0).astype(int)

    if 'is_home' in df.columns:
        X['is_home'] = df['is_home'].astype(int)

    return X, y, df


def chronological_split(X, y, df, test_size=0.2):
    """Split data chronologically."""
    sorted_idx = df['game_date'].argsort()
    X = X.iloc[sorted_idx].reset_index(drop=True)
    y = y.iloc[sorted_idx].reset_index(drop=True)
    dates = df['game_date'].iloc[sorted_idx].reset_index(drop=True)

    split_idx = int(len(X) * (1 - test_size))
    split_date = dates.iloc[split_idx]

    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    print(f"\nChronological Split:")
    print(f"  Train: {len(X_train):,} games (before {split_date})")
    print(f"  Test:  {len(X_test):,} games (from {split_date})")
    print(f"  Train FAILURE rate: {y_train.mean():.1%}")
    print(f"  Test FAILURE rate:  {y_test.mean():.1%}")

    return X_train, X_test, y_train, y_test


def train_model(X_train, y_train, X_test, y_test):
    """Train XGBoost classifier optimized for imbalanced data."""

    print("\nTraining XGBoost model (optimized for failures)...")

    X_train = X_train.fillna(-999)
    X_test = X_test.fillna(-999)

    # Calculate scale_pos_weight for imbalanced classes
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos_weight = neg_count / pos_count

    print(f"  Class balance: {pos_count:,} failures vs {neg_count:,} wins")
    print(f"  scale_pos_weight: {scale_pos_weight:.2f}")

    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'aucpr',  # Better for imbalanced data
        'max_depth': 4,
        'learning_rate': 0.03,
        'n_estimators': 300,
        'subsample': 0.7,
        'colsample_bytree': 0.7,
        'min_child_weight': 20,
        'reg_alpha': 0.5,
        'reg_lambda': 2.0,
        'scale_pos_weight': scale_pos_weight,
        'random_state': 42,
        'n_jobs': -1,
    }

    model = xgb.XGBClassifier(**params)
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    print(f"  Training complete")

    return model


def evaluate_model(model, X_train, y_train, X_test, y_test):
    """Evaluate model with focus on failure detection."""

    print("\n" + "=" * 60)
    print("MODEL EVALUATION (Predicting FAILURES)")
    print("=" * 60)

    X_train = X_train.fillna(-999)
    X_test = X_test.fillna(-999)

    y_test_pred = model.predict(X_test)
    y_test_proba = model.predict_proba(X_test)[:, 1]

    print("\nTest Set Metrics:")
    print(f"  Accuracy:  {accuracy_score(y_test, y_test_pred):.3f}")
    print(f"  Precision: {precision_score(y_test, y_test_pred):.3f} (of predicted failures, how many were real)")
    print(f"  Recall:    {recall_score(y_test, y_test_pred):.3f} (of real failures, how many did we catch)")
    print(f"  F1 Score:  {f1_score(y_test, y_test_pred):.3f}")
    print(f"  ROC AUC:   {roc_auc_score(y_test, y_test_proba):.3f}")
    print(f"  PR AUC:    {average_precision_score(y_test, y_test_proba):.3f}")

    cm = confusion_matrix(y_test, y_test_pred)
    print(f"\nConfusion Matrix (Failure = Positive):")
    print(f"  Predicted:    WIN    FAIL")
    print(f"  Actual WIN:  {cm[0,0]:>5,}  {cm[0,1]:>5,}")
    print(f"  Actual FAIL: {cm[1,0]:>5,}  {cm[1,1]:>5,}")

    # Calibration by predicted failure probability
    print("\n" + "-" * 60)
    print("CALIBRATION BY PREDICTED FAILURE PROBABILITY")
    print("-" * 60)

    df_eval = pd.DataFrame({
        'y_true': y_test.values,
        'y_proba': y_test_proba
    })

    df_eval['prob_bin'] = pd.cut(df_eval['y_proba'],
                                  bins=[0, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 1.0],
                                  labels=['<15%', '15-20%', '20-25%', '25-30%', '30-35%', '35-40%', '40-50%', '>50%'])

    calibration = df_eval.groupby('prob_bin', observed=True).agg({
        'y_true': ['count', 'mean']
    }).round(3)
    calibration.columns = ['count', 'actual_fail_rate']
    calibration = calibration[calibration['count'] >= 10]

    print(f"{'Pred Fail Prob':<15} {'Games':>8} {'Actual Fail%':>14} {'Win Rate':>10}")
    for idx, row in calibration.iterrows():
        win_rate = 1 - row['actual_fail_rate']
        print(f"{str(idx):<15} {int(row['count']):>8,} {row['actual_fail_rate']:>13.1%} {win_rate:>9.1%}")

    return y_test_proba


def analyze_feature_importance(model, X):
    """Analyze feature importance for failure prediction."""

    print("\n" + "=" * 60)
    print("FEATURE IMPORTANCE FOR FAILURE PREDICTION (Top 25)")
    print("=" * 60)

    importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print(f"{'Feature':<45} {'Importance':>12}")
    print("-" * 57)
    for _, row in importance.head(25).iterrows():
        bar = "#" * int(row['importance'] * 100)
        print(f"{row['feature']:<45} {row['importance']:>10.4f}  {bar}")

    return importance


def backtest_avoid_strategy(y_test, y_proba, df_test):
    """Backtest strategy: AVOID games with high failure probability."""

    print("\n" + "=" * 60)
    print("BACKTEST: AVOID HIGH FAILURE RISK GAMES")
    print("=" * 60)

    # Get actual win/loss from original labels
    # y_test = 1 means failure, so win = (1 - y_test)

    # Standard teaser odds (-110)
    profit_per_win = 100 / 110

    # Baseline: bet all games
    total_games = len(y_test)
    all_failures = y_test.sum()
    all_wins = total_games - all_failures
    all_profit = all_wins * profit_per_win - all_failures
    all_roi = all_profit / total_games

    print(f"\nBASELINE (bet all {total_games:,} games):")
    print(f"  Wins: {all_wins:,}  Failures: {all_failures:,}")
    print(f"  Win Rate: {all_wins/total_games:.1%}")
    print(f"  Profit: {all_profit:+.1f} units")
    print(f"  ROI: {all_roi:+.1%}")

    print("\n" + "-" * 60)
    print("AVOID STRATEGY RESULTS")
    print("-" * 60)
    print(f"{'Avoid If P(Fail)>':<18} {'Bets':>7} {'Avoided':>8} {'Wins':>7} {'Win%':>7} {'Profit':>10} {'ROI':>8}")
    print("-" * 60)

    for threshold in [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]:
        # Avoid games where P(failure) > threshold
        avoid_mask = y_proba > threshold
        bet_mask = ~avoid_mask

        n_bets = bet_mask.sum()
        n_avoided = avoid_mask.sum()

        if n_bets == 0:
            continue

        # Calculate results on games we bet
        failures_in_bets = y_test.values[bet_mask].sum()
        wins_in_bets = n_bets - failures_in_bets
        win_rate = wins_in_bets / n_bets

        profit = wins_in_bets * profit_per_win - failures_in_bets
        roi = profit / n_bets

        # How many failures did we successfully avoid?
        failures_avoided = y_test.values[avoid_mask].sum()
        avoid_accuracy = failures_avoided / n_avoided if n_avoided > 0 else 0

        print(f"{threshold:>17.0%} {n_bets:>7,} {n_avoided:>8,} {wins_in_bets:>7,} {win_rate:>6.1%} {profit:>+10.1f} {roi:>+7.1%}")

    # Detailed analysis at optimal threshold
    print("\n" + "-" * 60)
    print("DETAILED ANALYSIS: Avoid when P(Fail) > 30%")
    print("-" * 60)

    threshold = 0.30
    avoid_mask = y_proba > threshold
    bet_mask = ~avoid_mask

    avoided_games = y_test.values[avoid_mask]
    bet_games = y_test.values[bet_mask]

    print(f"\nGames we AVOIDED ({avoid_mask.sum():,} total):")
    print(f"  Actual failures in avoided: {avoided_games.sum():,} ({avoided_games.mean():.1%})")
    print(f"  Actual wins in avoided:     {len(avoided_games) - avoided_games.sum():,} ({1-avoided_games.mean():.1%})")
    print(f"  --> Successfully avoided {avoided_games.sum():,} failures!")

    print(f"\nGames we BET ({bet_mask.sum():,} total):")
    print(f"  Actual failures: {bet_games.sum():,} ({bet_games.mean():.1%})")
    print(f"  Actual wins:     {len(bet_games) - bet_games.sum():,} ({1-bet_games.mean():.1%})")

    # Value of avoided failures
    avoided_loss = avoided_games.sum()  # Each avoided failure saves 1 unit
    missed_wins = len(avoided_games) - avoided_games.sum()
    missed_profit = missed_wins * profit_per_win
    net_value = avoided_loss - missed_profit

    print(f"\nValue Analysis:")
    print(f"  Losses avoided: {avoided_loss:,} units saved")
    print(f"  Wins missed:    {missed_profit:.1f} units forgone")
    print(f"  Net value:      {net_value:+.1f} units")


def main():
    print("=" * 60)
    print("TEASER +8 FAILURE PREDICTION MODEL")
    print("=" * 60)
    print("Goal: Identify games to AVOID (the ~23% that fail)")
    print("=" * 60)

    df = load_data()
    X, y, df = prepare_features(df)
    X_train, X_test, y_train, y_test = chronological_split(X, y, df)

    model = train_model(X_train, y_train, X_test, y_test)
    y_proba = evaluate_model(model, X_train, y_train, X_test, y_test)
    importance = analyze_feature_importance(model, X)

    # Get test set dates for analysis
    sorted_idx = df['game_date'].argsort()
    split_idx = int(len(df) * 0.8)
    df_test = df.iloc[sorted_idx].iloc[split_idx:].reset_index(drop=True)

    backtest_avoid_strategy(y_test, y_proba, df_test)

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)

    return model, importance


if __name__ == "__main__":
    model, importance = main()
