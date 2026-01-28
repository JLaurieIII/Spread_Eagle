"""
================================================================================
CBB Over/Under Prediction Model
================================================================================

PURPOSE:
    Train ML models to predict college basketball game totals and generate
    probability distributions for Over/Under betting decisions.

OUTPUTS:
    - Point estimate of expected total points
    - Standard deviation / uncertainty estimate
    - Probability distribution: P(Total > X) for any threshold X
    - Calibrated probabilities at the Vegas line

APPROACH:
    1. Train XGBoost regressor to predict total points
    2. Estimate prediction uncertainty using residual analysis
    3. Assume normal distribution around predicted mean
    4. Calculate P(Total > X) = 1 - CDF(X | mean, std)

USAGE:
    python -m spread_eagle.ml.cbb_ou_model

================================================================================
"""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import psycopg2
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

import xgboost as xgb
import joblib

warnings.filterwarnings("ignore")


# =============================================================================
# CONFIGURATION
# =============================================================================

DB_CONFIG = {
    "host": "spread-eagle-db.cbwyw8ky62xm.us-east-2.rds.amazonaws.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "Sport4788!",
}

# dbt schema where models are materialized
DBT_SCHEMA = "marts_cbb"

# Feature columns used for training (order matters for model)
# Note: PostgreSQL lowercases column names, so L3/L5/L10 become l3/l5/l10
FEATURE_COLS = [
    # Vegas line (strong baseline predictor)
    "vegas_total",
    "vegas_line_movement",

    # Home team rolling stats - Points
    "home_avg_pts_scored_l3",
    "home_avg_pts_scored_l5",
    "home_avg_pts_scored_l10",
    "home_avg_pts_allowed_l5",
    "home_avg_pts_allowed_l10",
    "home_avg_total_pts_l5",
    "home_avg_total_pts_l10",
    "home_stddev_pts_scored_l5",
    "home_stddev_pts_allowed_l5",
    "home_stddev_total_pts_l5",

    # Home team rolling stats - Pace & Efficiency
    "home_avg_pace_l5",
    "home_avg_pace_l10",
    "home_stddev_pace_l5",
    "home_avg_off_rating_l5",
    "home_avg_off_rating_l10",
    "home_avg_def_rating_l5",
    "home_avg_def_rating_l10",
    "home_avg_net_rating_l5",

    # Home team rolling stats - Shooting & Style
    "home_avg_efg_pct_l5",
    "home_avg_fg3_pct_l5",
    "home_avg_oreb_pct_l5",
    "home_avg_tov_ratio_l5",
    "home_avg_fastbreak_l5",
    "home_avg_paint_pts_l5",

    # Away team rolling stats - Points
    "away_avg_pts_scored_l3",
    "away_avg_pts_scored_l5",
    "away_avg_pts_scored_l10",
    "away_avg_pts_allowed_l5",
    "away_avg_pts_allowed_l10",
    "away_avg_total_pts_l5",
    "away_avg_total_pts_l10",
    "away_stddev_pts_scored_l5",
    "away_stddev_pts_allowed_l5",
    "away_stddev_total_pts_l5",

    # Away team rolling stats - Pace & Efficiency
    "away_avg_pace_l5",
    "away_avg_pace_l10",
    "away_stddev_pace_l5",
    "away_avg_off_rating_l5",
    "away_avg_off_rating_l10",
    "away_avg_def_rating_l5",
    "away_avg_def_rating_l10",
    "away_avg_net_rating_l5",

    # Away team rolling stats - Shooting & Style
    "away_avg_efg_pct_l5",
    "away_avg_fg3_pct_l5",
    "away_avg_oreb_pct_l5",
    "away_avg_tov_ratio_l5",
    "away_avg_fastbreak_l5",
    "away_avg_paint_pts_l5",

    # Combined features
    "combined_avg_total_l5",
    "combined_avg_total_l10",
    "combined_avg_pace_l5",
    "combined_avg_pace_l10",
    "combined_avg_off_rating_l5",
    "combined_avg_def_rating_l5",
    "combined_avg_efg_l5",
    "combined_stddev_total_l5",
    "combined_stddev_pace_l5",

    # Matchup efficiency differentials
    "home_off_vs_away_def_l5",
    "away_off_vs_home_def_l5",
]

# Target column
TARGET_COL = "actual_total"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ProbabilityDistribution:
    """
    Represents the predicted probability distribution for a game's total.
    """
    game_id: int
    home_team: str
    away_team: str
    game_date: str

    # Vegas line
    vegas_total: float

    # Model predictions
    predicted_mean: float
    predicted_std: float

    # Probabilities at various thresholds
    prob_over_vegas: float  # P(Total > vegas_total)
    prob_curve: Dict[float, float]  # {threshold: P(Total > threshold)}

    # Confidence metrics
    model_edge: float  # predicted_mean - vegas_total
    confidence: str  # "high", "medium", "low" based on edge vs uncertainty


@dataclass
class ModelMetrics:
    """Training/evaluation metrics."""
    mae: float
    rmse: float
    r2: float
    over_accuracy: float  # % correct on over/under calls
    calibration_error: float  # avg |P(over) - actual_over_rate| by bin


# =============================================================================
# DATA LOADING
# =============================================================================

def load_training_data() -> pd.DataFrame:
    """
    Load ML feature data from the dbt-created fact table.
    Filters to completed games with sufficient history.
    """
    print("Loading training data from PostgreSQL...")

    conn = psycopg2.connect(**DB_CONFIG)

    query = f"""
    SELECT *
    FROM {DBT_SCHEMA}.fct_cbb__ml_features_ou
    WHERE is_completed = true
      AND has_sufficient_history = true
    ORDER BY game_date, game_id
    """

    df = pd.read_sql(query, conn)
    conn.close()

    print(f"  Loaded {len(df):,} completed games with sufficient history")
    print(f"  Date range: {df['game_date'].min()} to {df['game_date'].max()}")
    print(f"  Seasons: {sorted(df['season'].unique())}")

    return df


def load_upcoming_games() -> pd.DataFrame:
    """
    Load upcoming/scheduled games for inference.
    These have features but no actual_total yet.
    """
    print("Loading upcoming games for prediction...")

    conn = psycopg2.connect(**DB_CONFIG)

    query = f"""
    SELECT *
    FROM {DBT_SCHEMA}.fct_cbb__ml_features_ou
    WHERE is_completed = false
      AND has_minimum_history = true
      AND game_date >= CURRENT_DATE
    ORDER BY game_date, game_id
    """

    df = pd.read_sql(query, conn)
    conn.close()

    print(f"  Loaded {len(df):,} upcoming games")

    return df


# =============================================================================
# FEATURE ENGINEERING
# =============================================================================

def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Prepare feature matrix from raw data.
    Returns (X dataframe, list of feature names actually used).
    """
    # Use only features that exist in the data
    available_features = [c for c in FEATURE_COLS if c in df.columns]
    missing_features = [c for c in FEATURE_COLS if c not in df.columns]

    if missing_features:
        print(f"  Warning: {len(missing_features)} features not found: {missing_features[:5]}...")

    X = df[available_features].copy()

    # Fill missing values with median (robust to outliers)
    # For production, consider more sophisticated imputation
    X = X.fillna(X.median())

    print(f"  Using {len(available_features)} features")

    return X, available_features


# =============================================================================
# MODEL TRAINING
# =============================================================================

def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
) -> xgb.XGBRegressor:
    """
    Train XGBoost regressor to predict game totals.

    Hyperparameters tuned for:
    - Generalization (avoid overfitting to recent games)
    - Stable predictions (smooth probability curves)
    """
    print("\nTraining XGBoost model...")

    model = xgb.XGBRegressor(
        # Tree structure
        max_depth=5,
        min_child_weight=20,  # Regularization: require significant samples per leaf

        # Learning
        learning_rate=0.03,
        n_estimators=500,

        # Regularization
        subsample=0.7,
        colsample_bytree=0.7,
        reg_alpha=0.1,  # L1 regularization
        reg_lambda=1.0,  # L2 regularization

        # Other
        random_state=42,
        n_jobs=-1,
        early_stopping_rounds=50,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    print(f"  Best iteration: {model.best_iteration}")

    return model


def estimate_prediction_uncertainty(
    model: xgb.XGBRegressor,
    X: pd.DataFrame,
    y_true: pd.Series,
) -> float:
    """
    Estimate the standard deviation of prediction errors.
    This is used to create the probability distribution around predictions.

    We use a simple approach: global residual std.
    More sophisticated: heteroscedastic models, quantile regression.
    """
    y_pred = model.predict(X)
    residuals = y_true - y_pred

    # Use robust estimator (MAD-based) to reduce impact of outliers
    mad = np.median(np.abs(residuals - np.median(residuals)))
    robust_std = mad * 1.4826  # Convert MAD to std for normal dist

    # Also calculate regular std for comparison
    regular_std = np.std(residuals)

    print(f"\nUncertainty estimation:")
    print(f"  Regular std of residuals: {regular_std:.2f} points")
    print(f"  Robust std (MAD-based):   {robust_std:.2f} points")

    # Use the robust estimate
    return robust_std


# =============================================================================
# PROBABILITY CALCULATIONS
# =============================================================================

def calculate_probability_over(
    predicted_mean: float,
    predicted_std: float,
    threshold: float,
) -> float:
    """
    Calculate P(Total > threshold) assuming normal distribution.

    P(X > t) = 1 - CDF(t) = 1 - Phi((t - mean) / std)
    """
    if predicted_std <= 0:
        # Edge case: if std is 0, return deterministic result
        return 1.0 if predicted_mean > threshold else 0.0

    z_score = (threshold - predicted_mean) / predicted_std
    prob_under = stats.norm.cdf(z_score)
    prob_over = 1 - prob_under

    return prob_over


def generate_probability_curve(
    predicted_mean: float,
    predicted_std: float,
    vegas_total: float,
    n_points: int = 15,
) -> Dict[float, float]:
    """
    Generate P(Total > X) for a range of thresholds around the Vegas line.

    Returns dict: {threshold: probability}
    """
    # Generate thresholds: Vegas line +/- 25 points
    min_threshold = max(100, vegas_total - 25)
    max_threshold = vegas_total + 25

    thresholds = np.linspace(min_threshold, max_threshold, n_points)

    # Always include the exact Vegas line
    thresholds = np.unique(np.append(thresholds, vegas_total))
    thresholds = np.sort(thresholds)

    curve = {}
    for t in thresholds:
        prob = calculate_probability_over(predicted_mean, predicted_std, t)
        # Round threshold to .5 for cleaner output
        t_rounded = round(t * 2) / 2
        curve[t_rounded] = round(prob, 4)

    return curve


def determine_confidence_level(
    model_edge: float,
    predicted_std: float,
) -> str:
    """
    Determine confidence level based on edge relative to uncertainty.

    High: edge > 1.5 * std (strong signal)
    Medium: edge > 0.5 * std (moderate signal)
    Low: edge <= 0.5 * std (weak signal, close to noise)
    """
    if predicted_std <= 0:
        return "low"

    edge_ratio = abs(model_edge) / predicted_std

    if edge_ratio > 1.5:
        return "high"
    elif edge_ratio > 0.5:
        return "medium"
    else:
        return "low"


# =============================================================================
# EVALUATION
# =============================================================================

def evaluate_model(
    model: xgb.XGBRegressor,
    X: pd.DataFrame,
    y_true: pd.Series,
    vegas_totals: pd.Series,
    predicted_std: float,
) -> ModelMetrics:
    """
    Comprehensive model evaluation including calibration.
    """
    y_pred = model.predict(X)

    # Regression metrics
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)

    # Over/Under accuracy
    model_over_pred = y_pred > vegas_totals
    actual_over = y_true > vegas_totals
    over_accuracy = (model_over_pred == actual_over).mean()

    # Calibration: bin by predicted probability, check actual over rate
    probs = [
        calculate_probability_over(pred, predicted_std, vegas)
        for pred, vegas in zip(y_pred, vegas_totals)
    ]

    df_cal = pd.DataFrame({
        "prob_over": probs,
        "actual_over": actual_over.astype(int),
    })

    df_cal["prob_bin"] = pd.cut(df_cal["prob_over"], bins=[0, 0.3, 0.45, 0.55, 0.7, 1.0])

    calibration_errors = []
    for bin_label, group in df_cal.groupby("prob_bin", observed=True):
        if len(group) >= 20:
            expected = group["prob_over"].mean()
            actual = group["actual_over"].mean()
            calibration_errors.append(abs(expected - actual))

    avg_calibration_error = np.mean(calibration_errors) if calibration_errors else 0.0

    return ModelMetrics(
        mae=mae,
        rmse=rmse,
        r2=r2,
        over_accuracy=over_accuracy,
        calibration_error=avg_calibration_error,
    )


def print_evaluation_report(
    metrics: ModelMetrics,
    split_name: str = "Test",
) -> None:
    """Print formatted evaluation report."""
    print(f"\n{'=' * 60}")
    print(f"{split_name.upper()} SET EVALUATION")
    print("=" * 60)

    print(f"\nRegression Metrics:")
    print(f"  MAE:  {metrics.mae:.2f} points")
    print(f"  RMSE: {metrics.rmse:.2f} points")
    print(f"  R2:   {metrics.r2:.3f}")

    print(f"\nOver/Under Accuracy:")
    print(f"  Correct calls: {metrics.over_accuracy:.1%}")

    print(f"\nCalibration:")
    print(f"  Avg calibration error: {metrics.calibration_error:.3f}")


def print_feature_importance(
    model: xgb.XGBRegressor,
    feature_names: List[str],
    top_n: int = 20,
) -> None:
    """Print top features by importance."""
    print(f"\n{'=' * 60}")
    print("TOP FEATURES BY IMPORTANCE")
    print("=" * 60)

    importance = pd.DataFrame({
        "feature": feature_names,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)

    for i, row in importance.head(top_n).iterrows():
        bar = "#" * int(row["importance"] * 50)
        print(f"  {row['feature']:<40} {row['importance']:.4f} {bar}")


# =============================================================================
# PREDICTION / INFERENCE
# =============================================================================

def predict_game(
    model: xgb.XGBRegressor,
    game_features: pd.Series,
    game_info: pd.Series,
    predicted_std: float,
) -> ProbabilityDistribution:
    """
    Generate probability distribution for a single game.
    """
    # Get model prediction
    X = game_features.values.reshape(1, -1)
    predicted_mean = float(model.predict(X)[0])

    vegas_total = float(game_info["vegas_total"])

    # Calculate probability at Vegas line
    prob_over_vegas = calculate_probability_over(predicted_mean, predicted_std, vegas_total)

    # Generate full probability curve
    prob_curve = generate_probability_curve(predicted_mean, predicted_std, vegas_total)

    # Calculate edge and confidence
    model_edge = predicted_mean - vegas_total
    confidence = determine_confidence_level(model_edge, predicted_std)

    return ProbabilityDistribution(
        game_id=int(game_info["game_id"]),
        home_team=str(game_info.get("home_team", "Unknown")),
        away_team=str(game_info.get("away_team", "Unknown")),
        game_date=str(game_info["game_date"]),
        vegas_total=vegas_total,
        predicted_mean=round(predicted_mean, 1),
        predicted_std=round(predicted_std, 1),
        prob_over_vegas=round(prob_over_vegas, 4),
        prob_curve=prob_curve,
        model_edge=round(model_edge, 1),
        confidence=confidence,
    )


def predict_upcoming_games(
    model: xgb.XGBRegressor,
    df_upcoming: pd.DataFrame,
    feature_names: List[str],
    predicted_std: float,
) -> List[ProbabilityDistribution]:
    """
    Generate predictions for all upcoming games.
    """
    predictions = []

    for idx, row in df_upcoming.iterrows():
        game_features = row[feature_names].fillna(0)
        pred = predict_game(model, game_features, row, predicted_std)
        predictions.append(pred)

    return predictions


# =============================================================================
# OUTPUT FORMATTING
# =============================================================================

def format_prediction_for_display(pred: ProbabilityDistribution) -> str:
    """Format a single prediction for console output."""
    lines = [
        f"\n{'─' * 70}",
        f"  {pred.away_team} @ {pred.home_team}",
        f"  {pred.game_date}",
        f"{'─' * 70}",
        f"  Vegas Total:     {pred.vegas_total}",
        f"  Model Predicted: {pred.predicted_mean} (±{pred.predicted_std})",
        f"  Model Edge:      {pred.model_edge:+.1f} points",
        f"  Confidence:      {pred.confidence.upper()}",
        f"",
        f"  P(OVER {pred.vegas_total}): {pred.prob_over_vegas:.1%}",
        f"",
        f"  Probability Curve:",
    ]

    # Format probability curve
    for threshold, prob in sorted(pred.prob_curve.items()):
        bar = "#" * int(prob * 30)
        marker = " ← VEGAS" if threshold == pred.vegas_total else ""
        lines.append(f"    {threshold:>6.1f} pts: {prob:>5.1%} {bar}{marker}")

    return "\n".join(lines)


def export_predictions_json(
    predictions: List[ProbabilityDistribution],
    output_path: Path,
) -> None:
    """Export predictions to JSON for frontend consumption."""
    output = {
        "generated_at": datetime.now().isoformat(),
        "model_version": "cbb_ou_v1",
        "predictions": [
            {
                "game_id": p.game_id,
                "home_team": p.home_team,
                "away_team": p.away_team,
                "game_date": p.game_date,
                "vegas_total": p.vegas_total,
                "predicted_mean": p.predicted_mean,
                "predicted_std": p.predicted_std,
                "prob_over_vegas": p.prob_over_vegas,
                "model_edge": p.model_edge,
                "confidence": p.confidence,
                "probability_curve": p.prob_curve,
            }
            for p in predictions
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nExported predictions to: {output_path}")


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_training_pipeline() -> Tuple[xgb.XGBRegressor, List[str], float]:
    """
    Full training pipeline:
    1. Load data
    2. Split chronologically
    3. Train model
    4. Evaluate
    5. Return model artifacts
    """
    print("=" * 70)
    print("CBB OVER/UNDER MODEL TRAINING")
    print("=" * 70)

    # Load data
    df = load_training_data()

    if len(df) < 100:
        raise ValueError(f"Insufficient training data: {len(df)} games. Need at least 100.")

    # Prepare features
    X, feature_names = prepare_features(df)
    y = df[TARGET_COL]
    vegas = df["vegas_total"]

    # Chronological train/val/test split (60/20/20)
    n = len(df)
    train_end = int(n * 0.6)
    val_end = int(n * 0.8)

    X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
    X_val, y_val = X.iloc[train_end:val_end], y.iloc[train_end:val_end]
    X_test, y_test = X.iloc[val_end:], y.iloc[val_end:]
    vegas_test = vegas.iloc[val_end:]

    print(f"\nData splits:")
    print(f"  Train: {len(X_train):,} games ({df.iloc[:train_end]['game_date'].min()} to {df.iloc[:train_end]['game_date'].max()})")
    print(f"  Val:   {len(X_val):,} games")
    print(f"  Test:  {len(X_test):,} games ({df.iloc[val_end:]['game_date'].min()} to {df.iloc[val_end:]['game_date'].max()})")

    # Train model
    model = train_model(X_train, y_train, X_val, y_val)

    # Estimate uncertainty from validation set
    predicted_std = estimate_prediction_uncertainty(model, X_val, y_val)

    # Evaluate on test set
    test_metrics = evaluate_model(model, X_test, y_test, vegas_test, predicted_std)
    print_evaluation_report(test_metrics, "Test")

    # Feature importance
    print_feature_importance(model, feature_names)

    # Calibration analysis
    print(f"\n{'=' * 60}")
    print("CALIBRATION BY PROBABILITY BIN")
    print("=" * 60)

    y_pred_test = model.predict(X_test)
    probs = [
        calculate_probability_over(pred, predicted_std, vegas)
        for pred, vegas in zip(y_pred_test, vegas_test)
    ]

    df_cal = pd.DataFrame({
        "prob_over": probs,
        "actual_over": (y_test > vegas_test).astype(int),
    })
    df_cal["prob_bin"] = pd.cut(
        df_cal["prob_over"],
        bins=[0, 0.35, 0.45, 0.55, 0.65, 1.0],
        labels=["<35%", "35-45%", "45-55%", "55-65%", ">65%"],
    )

    print(f"\n{'Bin':<12} {'Games':>8} {'Avg P(O)':>10} {'Actual O%':>12} {'Error':>10}")
    print("-" * 55)

    for bin_label in ["<35%", "35-45%", "45-55%", "55-65%", ">65%"]:
        group = df_cal[df_cal["prob_bin"] == bin_label]
        if len(group) >= 10:
            avg_prob = group["prob_over"].mean()
            actual_rate = group["actual_over"].mean()
            error = actual_rate - avg_prob
            print(f"{bin_label:<12} {len(group):>8,} {avg_prob:>9.1%} {actual_rate:>11.1%} {error:>+9.1%}")

    return model, feature_names, predicted_std


def run_inference_pipeline(
    model: xgb.XGBRegressor,
    feature_names: List[str],
    predicted_std: float,
) -> List[ProbabilityDistribution]:
    """
    Run inference on upcoming games.
    """
    print(f"\n{'=' * 70}")
    print("GENERATING PREDICTIONS FOR UPCOMING GAMES")
    print("=" * 70)

    df_upcoming = load_upcoming_games()

    if len(df_upcoming) == 0:
        print("No upcoming games found.")
        return []

    predictions = predict_upcoming_games(model, df_upcoming, feature_names, predicted_std)

    # Sort by confidence and edge
    predictions.sort(key=lambda p: abs(p.model_edge), reverse=True)

    # Display top predictions
    print(f"\nTop predictions by model edge:")
    for pred in predictions[:10]:
        print(format_prediction_for_display(pred))

    return predictions


def main() -> None:
    """Main entry point."""
    # Train model
    model, feature_names, predicted_std = run_training_pipeline()

    # Save model artifacts
    output_dir = Path("models/cbb_ou")
    output_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, output_dir / "model.joblib")
    joblib.dump(feature_names, output_dir / "feature_names.joblib")
    joblib.dump(predicted_std, output_dir / "predicted_std.joblib")
    print(f"\nModel artifacts saved to: {output_dir}")

    # Run inference on upcoming games
    predictions = run_inference_pipeline(model, feature_names, predicted_std)

    # Export predictions
    if predictions:
        export_predictions_json(
            predictions,
            Path("data/predictions/cbb_ou_predictions.json"),
        )

    print(f"\n{'=' * 70}")
    print("PIPELINE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
