# ML Pipeline Design

How dbt models feed ML predictions.

---

## The Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                        dbt MODELS                                 │
│                                                                   │
│  STAGING          INTERMEDIATE           MARTS                    │
│  ────────         ────────────           ─────                    │
│  Raw data    →    Feature eng    →    ML-ready tables            │
│                                                                   │
│  stg_games        int_game_team_lines    fct_matchup_snapshot    │
│  stg_lines        int_rolling_form       fct_variance_profile    │
│  stg_teams        int_rest_schedule      fct_teaser_candidates   │
│                                          fct_upcoming_predictions │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     ML TRAINING                                   │
│                                                                   │
│  1. Query fct_matchup_snapshot (historical completed games)       │
│  2. Split chronologically (80% train, 20% validation)            │
│  3. Train XGBoost classifier                                      │
│  4. Evaluate accuracy, calibration                                │
│  5. Save model artifact to disk                                   │
│                                                                   │
│  Features: team_ats_l10_avg, opp_ats_l10_avg, delta_*, etc.      │
│  Label: is_cover (boolean)                                        │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     ML SCORING                                    │
│                                                                   │
│  1. Query fct_upcoming_predictions (future games with lines)      │
│  2. Load trained model                                            │
│  3. Generate cover probabilities                                  │
│  4. Output: game_id, team, spread, p_cover, confidence, rating    │
│                                                                   │
│  Result goes to: API → Frontend                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## dbt Views → ML Features Mapping

### For ATS Prediction Model

| dbt Column | ML Feature Name | Description |
|------------|-----------------|-------------|
| `is_home` | `is_home_int` | 1 if home, 0 if away |
| `spread_close_for_team` | `spread` | Line from team perspective |
| `team_ats_l5_avg` | `team_ats_l5` | Team's 5-game ATS avg |
| `team_ats_l10_avg` | `team_ats_l10` | Team's 10-game ATS avg |
| `team_cover_l5` | `team_cover_rate_5` | Team's cover rate (5g) |
| `team_cover_l10` | `team_cover_rate_10` | Team's cover rate (10g) |
| `opp_ats_l10_avg` | `opp_ats_l10` | Opponent's ATS avg |
| `opp_cover_l10` | `opp_cover_rate_10` | Opponent's cover rate |
| `delta_ats_l10` | `delta_ats` | Team ATS - Opp ATS |
| `delta_margin_l10` | `delta_margin` | Team margin - Opp margin |

### For Teaser Model (Additional Features)

| dbt Column | ML Feature Name | Description |
|------------|-----------------|-------------|
| `ats_margin_std_l20` | `volatility` | KEY: Team's ATS consistency |
| `pct_within_7_pts` | `teaser_friendly` | % games within teaser range |
| `opp_ats_margin_std_l20` | `opp_volatility` | Opponent's consistency |
| `rest_days` | `rest` | Days since last game |
| `is_back_to_back` | `b2b` | Back-to-back flag |

---

## Model Architecture

### Model 1: ATS Classifier (Current)

```python
Purpose: Predict P(cover) for any game
Input: Matchup features from fct_matchup_snapshot
Output: Probability 0-1

XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    objective='binary:logistic'
)

Training data: All completed games with rolling features
Label: is_cover (True/False)
```

### Model 2: Teaser Classifier (To Build)

```python
Purpose: Predict P(cover at teased line) for low-vol teams
Input: Matchup features + variance features
Output: Probability 0-1

Additional preprocessing:
- Filter to low-volatility candidates only
- Adjust spread by teaser points before scoring
- Separate models for 6pt and 7pt teasers?

Training data: Only teams with ats_margin_std_l20 < 8
Label: would_cover_if_teased_6pts (computed from ats_margin)
```

### Model 3: Margin Regressor (Future)

```python
Purpose: Predict actual ATS margin (not just cover/not)
Input: Same matchup features
Output: Continuous margin estimate

XGBRegressor(...)

Use case: Build probability distributions for teasers
- If predicted margin = 4 with std = 3
- P(cover at +7) = P(actual margin > -7) = very high
```

---

## Feature Engineering in dbt vs Python

### Do in dbt (SQL)
- Rolling aggregations (avg, std, min, max)
- Window functions for "as-of" calculations
- Joins between tables
- Date calculations (rest days)
- Flag computations (is_back_to_back)

### Do in Python (ML script)
- Type conversions (bool → int)
- Null handling (fillna, dropna)
- Feature scaling (if needed)
- Feature interactions (team_ats * opp_ats)
- Model-specific transformations

---

## Data Contracts

### fct_matchup_snapshot (Training Data)

```sql
Required columns for ML:
- game_id (PK)
- game_date (for chronological split)
- team_id, opponent_id
- is_home
- spread_close_for_team
- team_ats_l5_avg, team_ats_l10_avg
- team_cover_l5, team_cover_l10
- team_margin_l5_avg, team_margin_l10_avg
- opp_ats_l5_avg, opp_ats_l10_avg
- opp_cover_l5, opp_cover_l10
- delta_ats_l5, delta_ats_l10
- is_cover (LABEL - must be NOT NULL for training)
```

### fct_upcoming_predictions (Scoring Data)

```sql
Required columns for ML:
- Same features as above
- is_cover should be NULL (game not played)
- spread_close_for_team must be NOT NULL (need a line)
```

### fct_variance_profile (Teaser Features)

```sql
Required columns:
- team_id
- ats_margin_std_l20      -- Volatility measure
- ats_margin_mean_l20     -- Central tendency
- pct_games_within_7_pts  -- Teaser success rate
- sample_size             -- Games in window
```

---

## Pipeline Orchestration

### Daily Flow

```
6:00 AM  - Airflow triggers
6:01 AM  - Ingest new game results
6:05 AM  - Ingest updated lines
6:10 AM  - dbt run (staging → intermediate → marts)
6:25 AM  - Load trained model
6:26 AM  - Query fct_upcoming_predictions
6:27 AM  - Generate predictions
6:28 AM  - Write to predictions table or API
6:30 AM  - Send alerts for high-confidence plays
```

### Model Retraining (Weekly)

```
Sunday 2:00 AM - Retrain on full history
- Query all historical data
- Train new model
- Compare to previous model
- If better: deploy; else: keep old
- Log metrics to tracking table
```

---

## Error Handling

### Data Quality Checks

```python
# Before training
assert df['is_cover'].notna().all(), "Labels can't be null"
assert df['spread_close_for_team'].notna().all(), "Need spreads"
assert len(df) >= 1000, "Need sufficient training data"

# Before scoring
assert len(upcoming) > 0, "No games to predict"
assert upcoming['spread_close_for_team'].notna().all(), "Missing lines"
```

### Model Quality Checks

```python
# After training
assert accuracy > 0.48, "Model worse than random"
assert accuracy < 0.60, "Suspiciously good - check for leakage"

# Calibration
# If model says 60%, should win ~60% of the time
```

---

## Next Steps

1. **Build fct_variance_profile** for both CFB and CBB
2. **Create teaser label** in training data
3. **Train teaser-specific model**
4. **Backtest teaser strategy** on historical data
5. **Build Airflow DAG** to automate daily runs
