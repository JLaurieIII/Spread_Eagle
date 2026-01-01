"""
Matchup-Level Teaser Model

Uses BOTH teams' features to predict game outcomes.
Key insight: Low-variance matchups (both teams stable) should be safer.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score
import xgboost as xgb
import psycopg2
import warnings
warnings.filterwarnings('ignore')


def load_data():
    """Load the matchup dataset."""
    print("Loading matchup data from PostgreSQL...")

    conn = psycopg2.connect(
        host='localhost', port=5432, database='spread_eagle',
        user='dbeaver_user', password='Sport4788!'
    )

    query = """
    SELECT *
    FROM dbt_dev.fct_cbb_teaser_matchup_dataset
    WHERE both_teams_win_teased_8 IS NOT NULL
    ORDER BY game_date, game_id
    """

    df = pd.read_sql(query, conn)
    conn.close()

    print(f"Loaded {len(df):,} games")
    return df


def prepare_features(df):
    """Prepare matchup features."""

    feature_cols = [
        # Home team features
        'home_stddev_cover_last5', 'home_stddev_cover_last10', 'home_stddev_cover_last20',
        'home_within_7_rate_last10', 'home_within_10_rate_last10',
        'home_mean_cover_last10',
        'home_tail_8_rate_last10', 'home_tail_10_rate_last10', 'home_tail_15_rate_last10',
        'home_teaser_8_survival', 'home_teaser_10_survival',
        'home_worst_cover_last10', 'home_blowout_rate_last10',
        'home_ats_rate_last5', 'home_ats_rate_last10', 'home_ats_streak',
        'home_variance_contraction',

        # Away team features
        'away_stddev_cover_last5', 'away_stddev_cover_last10', 'away_stddev_cover_last20',
        'away_within_7_rate_last10', 'away_within_10_rate_last10',
        'away_mean_cover_last10',
        'away_tail_8_rate_last10', 'away_tail_10_rate_last10', 'away_tail_15_rate_last10',
        'away_teaser_8_survival', 'away_teaser_10_survival',
        'away_worst_cover_last10', 'away_blowout_rate_last10',
        'away_ats_rate_last5', 'away_ats_rate_last10', 'away_ats_streak',
        'away_variance_contraction',

        # Combined matchup features
        'combined_stddev_cover_last10', 'avg_volatility_last10', 'max_volatility_last10',
        'combined_within_7_rate', 'combined_within_10_rate',
        'matchup_teaser_8_survival', 'matchup_teaser_10_survival',
        'matchup_blowout_risk', 'combined_tail_10_risk',

        # Game context
        'closing_spread_home', 'closing_total',
    ]

    available_cols = [c for c in feature_cols if c in df.columns]
    print(f"Using {len(available_cols)} features")

    X = df[available_cols].copy()

    # Add categorical features
    if 'teaser_matchup_quality' in df.columns:
        quality_map = {'premium': 3, 'good': 2, 'fair': 1, 'avoid': 0}
        X['matchup_quality_score'] = df['teaser_matchup_quality'].map(quality_map).fillna(0)

    if 'both_teams_stabilizing' in df.columns:
        X['both_stabilizing'] = df['both_teams_stabilizing'].astype(int)

    if 'trend_clash' in df.columns:
        X['trend_clash'] = df['trend_clash'].astype(int)

    return X, df


def run_analysis(df, X):
    """Run multiple prediction tasks."""

    print("\n" + "=" * 70)
    print("MATCHUP ANALYSIS")
    print("=" * 70)

    # Chronological split
    sorted_idx = df['game_date'].argsort()
    X = X.iloc[sorted_idx].reset_index(drop=True)
    df = df.iloc[sorted_idx].reset_index(drop=True)

    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    df_train, df_test = df.iloc[:split_idx], df.iloc[split_idx:]

    print(f"\nTrain: {len(X_train):,} games | Test: {len(X_test):,} games")

    # Fill missing
    X_train = X_train.fillna(-999)
    X_test = X_test.fillna(-999)

    # =====================================================
    # TASK 1: Predict if BOTH teams win +8 teaser
    # =====================================================
    print("\n" + "-" * 70)
    print("TASK 1: Predict BOTH teams win +8 teaser (parlay)")
    print("-" * 70)

    y1_train = df_train['both_teams_win_teased_8'].astype(int)
    y1_test = df_test['both_teams_win_teased_8'].astype(int)

    print(f"Train parlay win rate: {y1_train.mean():.1%}")
    print(f"Test parlay win rate:  {y1_test.mean():.1%}")

    model1 = xgb.XGBClassifier(
        max_depth=4, learning_rate=0.03, n_estimators=200,
        subsample=0.7, colsample_bytree=0.7, min_child_weight=15,
        random_state=42, n_jobs=-1
    )
    model1.fit(X_train, y1_train, eval_set=[(X_test, y1_test)], verbose=False)

    y1_proba = model1.predict_proba(X_test)[:, 1]
    auc1 = roc_auc_score(y1_test, y1_proba)
    print(f"ROC AUC: {auc1:.3f}")

    # Calibration
    print("\nCalibration by predicted probability:")
    df_eval = pd.DataFrame({'y': y1_test.values, 'p': y1_proba})
    df_eval['bin'] = pd.cut(df_eval['p'], bins=[0, 0.4, 0.5, 0.55, 0.6, 0.65, 0.7, 1.0])

    for bin_label, group in df_eval.groupby('bin', observed=True):
        if len(group) >= 20:
            print(f"  {bin_label}: {len(group):>5} games, actual win rate: {group['y'].mean():.1%}")

    # =====================================================
    # TASK 2: Analyze by matchup quality tier
    # =====================================================
    print("\n" + "-" * 70)
    print("TASK 2: Results by Matchup Quality Tier")
    print("-" * 70)

    if 'teaser_matchup_quality' in df_test.columns:
        print(f"\n{'Quality':<12} {'Games':>7} {'Home+8':>8} {'Away+8':>8} {'Both+8':>8} {'Either+8':>9}")
        print("-" * 55)

        for quality in ['premium', 'good', 'fair', 'avoid']:
            mask = df_test['teaser_matchup_quality'] == quality
            subset = df_test[mask]

            if len(subset) < 10:
                continue

            home_win = subset['home_win_teased_8'].mean()
            away_win = subset['away_win_teased_8'].mean()
            both_win = subset['both_teams_win_teased_8'].mean()
            either_fail = 1 - both_win

            print(f"{quality:<12} {len(subset):>7,} {home_win:>7.1%} {away_win:>7.1%} {both_win:>7.1%} {either_fail:>8.1%}")

    # =====================================================
    # TASK 3: Feature importance
    # =====================================================
    print("\n" + "-" * 70)
    print("TOP FEATURES FOR PARLAY SUCCESS")
    print("-" * 70)

    importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model1.feature_importances_
    }).sort_values('importance', ascending=False)

    for _, row in importance.head(15).iterrows():
        print(f"  {row['feature']:<40} {row['importance']:.4f}")

    # =====================================================
    # TASK 4: Backtest selective betting
    # =====================================================
    print("\n" + "-" * 70)
    print("BACKTEST: Selective Parlay Betting")
    print("-" * 70)

    # Typical 2-team teaser parlay odds: -120 (bet 120 to win 100)
    # Win: +100/120 = +0.833 units
    # Lose: -1 unit
    profit_per_win = 100 / 120

    baseline_wins = y1_test.sum()
    baseline_losses = len(y1_test) - baseline_wins
    baseline_profit = baseline_wins * profit_per_win - baseline_losses
    baseline_roi = baseline_profit / len(y1_test)

    print(f"\nBaseline (bet all {len(y1_test):,} games):")
    print(f"  Win rate: {y1_test.mean():.1%}")
    print(f"  Profit:   {baseline_profit:+.1f} units")
    print(f"  ROI:      {baseline_roi:+.1%}")

    print(f"\n{'Threshold':<12} {'Bets':>7} {'Wins':>7} {'Win%':>8} {'Profit':>10} {'ROI':>8}")
    print("-" * 55)

    for threshold in [0.55, 0.60, 0.65, 0.70]:
        mask = y1_proba >= threshold
        n_bets = mask.sum()
        if n_bets < 10:
            continue

        wins = y1_test.values[mask].sum()
        losses = n_bets - wins
        win_rate = wins / n_bets
        profit = wins * profit_per_win - losses
        roi = profit / n_bets

        print(f"P >= {threshold:.0%}     {n_bets:>7,} {wins:>7,} {win_rate:>7.1%} {profit:>+10.1f} {roi:>+7.1%}")

    return model1, importance


def main():
    print("=" * 70)
    print("MATCHUP-LEVEL TEASER ANALYSIS")
    print("=" * 70)

    df = load_data()
    X, df = prepare_features(df)
    model, importance = run_analysis(df, X)

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

    return model, importance


if __name__ == "__main__":
    model, importance = main()
