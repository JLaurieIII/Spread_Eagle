# CBB Over/Under ML System Architecture

## Executive Summary

We're building a machine learning system that predicts college basketball game totals (Over/Under) by:
1. Ingesting per-game statistics and betting lines
2. Computing rolling features that capture team form/trends
3. Training models to predict total points scored
4. Generating probability distributions to inform betting decisions

---

## 1. Raw Data Foundation

### What We Have

| Source | Records | Description |
|--------|---------|-------------|
| `cbb.game_team_stats` | 28,095 games | 97 columns of per-game team performance |
| `cbb.betting_lines` | 25,082 games | Spreads, totals, moneylines from multiple providers |
| **Games with BOTH** | 24,752 | Our usable training set |

### Key Raw Stats (per game, per team)

**Scoring & Efficiency:**
- `team_stats_points_total` - Total points scored
- `team_stats_rating` - Offensive rating (points per 100 possessions)
- `team_stats_true_shooting` - True shooting percentage
- `pace` - Game tempo (possessions per 40 minutes)

**Four Factors (proven predictors):**
- `team_stats_four_factors_effective_field_goal_pct` - eFG%
- `team_stats_four_factors_turnover_ratio` - TOV%
- `team_stats_four_factors_offensive_rebound_pct` - OREB%
- `team_stats_four_factors_free_throw_rate` - FT rate

**Style Indicators:**
- `team_stats_points_fast_break` - Fast break points
- `team_stats_points_in_paint` - Paint points
- `team_stats_three_point_field_goals_pct` - 3PT%

**Opponent Stats:** Mirror columns for opponent (what they allowed)

### Betting Lines
- **Bovada**: 2,230 lines (primary target - most liquid)
- **ESPN BET**: 17,634 lines (backup/comparison)
- Includes: spread, over_under, opening lines, moneylines

---

## 2. Feature Engineering Pipeline (dbt)

### Layer 1: Staging (`stg_cbb__*`)
**Purpose:** Clean raw data, standardize types, add computed fields

```
Raw Tables → Staging Views
- Parse dates from timestamps
- Rename columns for consistency
- Filter bad data
```

### Layer 2: Intermediate (`int_cbb__*`)
**Purpose:** Transform data into ML-ready features

**`int_cbb__team_game_stats`** (1 row per game per team)
- Consolidate team stats into clean structure
- Calculate derived metrics (net rating, total points, etc.)

**`int_cbb__team_rolling_stats`** (CRITICAL for ML)
- Calculate rolling windows: L3, L5, L10 (last 3/5/10 games)
- **Key Design:** EXCLUDES current game to prevent data leakage
- Window functions: `ROWS BETWEEN N PRECEDING AND 1 PRECEDING`
- Partitioned by team + season (resets each year)

Rolling features generated:
- `avg_points_scored_L5` - Average points scored last 5 games
- `stddev_points_scored_L5` - Scoring consistency
- `avg_pace_L5` - Tempo trend
- `avg_off_rating_L5` - Offensive efficiency trend
- `avg_def_rating_L5` - Defensive efficiency trend
- etc. (70+ rolling features)

**`int_cbb__game_betting_outcomes`**
- Join games with betting lines (Bovada primary)
- Calculate outcomes (over_hit, margin, etc.)

### Layer 3: Marts (`fct_cbb__*`)
**Purpose:** Final ML-ready tables

**`fct_cbb__ml_features_ou`** (our training table)
- 1 row per game
- Home team features (prefixed `home_*`)
- Away team features (prefixed `away_*`)
- Combined features (pace differential, efficiency matchups)
- Vegas line features (strong baseline signal)
- Target variables: `actual_total`, `over_hit`
- Filter flags: `has_sufficient_history`, `is_completed`

---

## 3. ML Model Architecture

### Problem Definition
**Task:** Predict total points scored in a game
**Output:**
- Point estimate (predicted total)
- Uncertainty estimate (std deviation)
- Probability distribution: P(Total > X) for any threshold X

### Why This Approach?
1. **Regression + Uncertainty** beats pure classification
   - Classification (over/under) loses information
   - Regression gives you predicted total AND distance from line
   - Uncertainty tells you how confident to be

2. **Vegas line as feature**
   - Markets are efficient; the line is a strong baseline
   - Our model learns to adjust the line based on recent form
   - Edge = Model Prediction - Vegas Line

### Model Selection: XGBoost Regressor
**Why XGBoost:**
- Handles tabular data well
- Built-in feature importance
- Robust to missing values
- Fast training/inference

**Hyperparameters (tuned for generalization):**
```python
{
    "max_depth": 5,          # Shallow trees prevent overfitting
    "min_child_weight": 20,  # Require substantial samples per leaf
    "learning_rate": 0.03,   # Slow learning for stability
    "subsample": 0.7,        # Bagging for variance reduction
    "colsample_bytree": 0.7, # Feature sampling
    "reg_alpha": 0.1,        # L1 regularization
    "reg_lambda": 1.0,       # L2 regularization
}
```

### Uncertainty Estimation
After training, we estimate prediction uncertainty from validation residuals:
```
predicted_std = MAD(residuals) * 1.4826  # Robust estimator
```
This gives us the typical error range for predictions.

### Probability Calculation
Assuming normal distribution around prediction:
```
P(Total > X) = 1 - CDF((X - predicted_mean) / predicted_std)
```

---

## 4. Training Pipeline

### Data Split (Chronological - CRITICAL)
```
Train:  60% oldest games (learn patterns)
Val:    20% middle games (tune hyperparameters, estimate uncertainty)
Test:   20% newest games (final evaluation)
```

**Why Chronological?**
- Random splits cause data leakage (future info leaks to past)
- Time-series nature: team form changes over time
- Mimics real deployment: train on past, predict future

### Evaluation Metrics

| Metric | What It Measures | Target |
|--------|-----------------|--------|
| MAE | Average prediction error (points) | < 12 points |
| RMSE | Penalizes large errors | < 15 points |
| R² | Variance explained | > 0.25 |
| O/U Accuracy | % correct over/under calls | > 52% |
| Calibration | Do probabilities match reality? | < 5% error |

### Current Status (ISSUE IDENTIFIED)
Recent training run showed:
- MAE: 14.73 points
- O/U Accuracy: **48.1%** (WORSE than random)
- R²: 0.150 (weak)

**Diagnosis:**
The model is performing below baseline. Possible causes:
1. Feature computation issue in dbt (need to verify rolling calcs)
2. Data leakage in the opposite direction (excluding too much info)
3. Overfitting on noise

---

## 5. Inference Pipeline

### For Upcoming Games
1. Load games where `is_completed = false` AND `has_sufficient_history = true`
2. Generate features using latest rolling stats (excludes unplayed game)
3. Run through trained model
4. Calculate probability distribution
5. Rank by edge/confidence

### Output Format
```json
{
    "game_id": 12345,
    "matchup": "Duke @ UNC",
    "vegas_total": 147.5,
    "predicted_total": 152.3,
    "model_edge": +4.8,
    "prob_over": 0.62,
    "confidence": "MEDIUM",
    "recommendation": "LEAN OVER"
}
```

---

## 6. Next Steps

### Immediate (Debug Current Issues)
1. Verify rolling window calculations in dbt are correct
2. Check `is_completed` flag logic (currently marking 0-0 games as completed)
3. Add baseline comparison (just use Vegas line as prediction)

### Short-term
1. Implement proper backtesting framework
2. Add variance/volatility features (high variance games = unpredictable)
3. Tune confidence thresholds based on historical performance

### Medium-term
1. Add spread prediction model
2. Implement ensemble approach
3. Track actual betting performance (ROI, units)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAW DATA LAYER                           │
│  cbb.game_team_stats (97 cols)   cbb.betting_lines (20 cols)   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      STAGING LAYER (dbt)                        │
│  stg_cbb__games  stg_cbb__game_team_stats  stg_cbb__betting_*   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   INTERMEDIATE LAYER (dbt)                      │
│  int_cbb__team_game_stats    int_cbb__team_rolling_stats        │
│  int_cbb__game_betting_outcomes                                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Rolling Windows: L3, L5, L10 (EXCLUDES current game)    │   │
│  │ Partitioned by: team_id, season                         │   │
│  │ Features: avg_*, stddev_* for scoring, pace, efficiency │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MARTS LAYER (dbt)                          │
│  fct_cbb__ml_features_ou (126 columns)                          │
│  - Home team rolling features (40+)                             │
│  - Away team rolling features (40+)                             │
│  - Combined/derived features (15+)                              │
│  - Vegas line features (4)                                      │
│  - Target: actual_total, over_hit                               │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        ML PIPELINE                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   Train     │───▶│   Model     │───▶│   Predictions       │ │
│  │  (60/20/20) │    │  XGBoost    │    │ + Uncertainty       │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Bovada as primary line source | Most liquid, sharpest lines |
| Rolling windows exclude current game | Prevents data leakage |
| Within-season partitioning | Teams change year-to-year |
| Chronological train/test split | Mimics real deployment |
| Regression + uncertainty | More information than classification |
| MAD-based std estimation | Robust to outliers |
