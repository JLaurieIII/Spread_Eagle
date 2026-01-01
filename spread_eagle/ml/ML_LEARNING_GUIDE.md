# Machine Learning Guide: Spread Eagle Predictions

This guide explains how the ML prediction system works and how to learn more.

---

## How This Script Works

### The Pipeline

```
1. LOAD TRAINING DATA
   └── Query marts_cfb.fct_cfb__matchup_snapshot
   └── Historical completed games with known outcomes

2. TRAIN MODEL
   └── XGBoost classifier
   └── Features: rolling ATS stats, cover rates, margins
   └── Label: did the team cover? (1 = yes, 0 = no)

3. LOAD UPCOMING GAMES
   └── Query marts_cfb.fct_cfb__upcoming_predictions
   └── Games with lines but no scores yet

4. PREDICT
   └── Model outputs probability of covering
   └── Display picks with confidence levels
```

---

## XGBoost: What Is It?

**XGBoost** (eXtreme Gradient Boosting) is an ensemble learning algorithm that builds many decision trees sequentially, where each tree corrects the errors of the previous ones.

### Why XGBoost for Sports Betting?

1. **Handles mixed features** - numeric and categorical
2. **Robust to outliers** - sports data has blowouts
3. **Feature importance** - tells you what matters
4. **Fast training** - can retrain daily
5. **Regularization** - prevents overfitting

### Key Hyperparameters

```python
XGBClassifier(
    n_estimators=100,    # Number of trees (more = slower but potentially better)
    max_depth=4,         # Tree depth (deeper = more complex patterns)
    learning_rate=0.1,   # Step size (smaller = more trees needed)
    random_state=42      # Reproducibility
)
```

**Tuning tips:**
- Start with `max_depth=3-6` for tabular data
- If overfitting, reduce `max_depth` or add `min_child_weight`
- If underfitting, increase `n_estimators` or `max_depth`

---

## Features We Use

### Team Rolling Stats (as of each game)

| Feature | Description |
|---------|-------------|
| `team_ats_l5_avg` | Average ATS margin over last 5 games |
| `team_ats_l10_avg` | Average ATS margin over last 10 games |
| `team_cover_l5` | Cover rate over last 5 games (0.0 - 1.0) |
| `team_cover_l10` | Cover rate over last 10 games |
| `team_margin_l5_avg` | Average score margin (straight up) |
| `team_win_l5` | Win rate over last 5 games |

### Opponent Rolling Stats

Same features but for the opponent.

### Delta Features

| Feature | Description |
|---------|-------------|
| `delta_ats_l10` | Team ATS avg - Opponent ATS avg |
| `delta_cover_l10` | Team cover rate - Opponent cover rate |
| `delta_margin_l10` | Team margin avg - Opponent margin avg |

**Intuition:** If Team A is +5 ATS and Opponent is -3 ATS, delta is +8. This suggests Team A has been outperforming expectations while Opponent has been underperforming.

### Other Features

| Feature | Description |
|---------|-------------|
| `is_home_int` | 1 if home, 0 if away |
| `spread_close_for_team` | The spread from this team's perspective |

---

## Training vs Validation Split

We use **chronological split** (not random):

```python
# 80% oldest games for training
# 20% newest games for validation
split_idx = int(len(X) * 0.8)
X_train = X.iloc[:split_idx]
X_val = X.iloc[split_idx:]
```

**Why chronological?**

Random splits cause **future leakage** - the model might learn patterns from games that happened AFTER the games it's trying to predict. In production, you only have past data.

---

## Interpreting Results

### Accuracy

```
Validation Accuracy: 52.3%
(Baseline ~50% - markets are efficient)
```

- **50%** = random guessing (coin flip)
- **52-53%** = slight edge (enough to be profitable long-term)
- **55%+** = suspiciously good (check for leakage)

### Feature Importance

```
spread_close_for_team     ########## 0.187
team_ats_l10_avg          #######    0.142
delta_ats_l10             ######     0.118
...
```

Higher importance = feature has more influence on predictions.

### Confidence Levels

```
LEAN       = confidence < 15%   (barely favors one side)
PLAY       = confidence 15-30%  (moderate edge)
STRONG PLAY = confidence > 30%  (model is confident)
```

**Warning:** High confidence doesn't guarantee wins. It means the model sees a pattern, but markets are smart.

---

## Learning More: XGBoost

### Official Documentation
- https://xgboost.readthedocs.io/

### Great Tutorials
1. **StatQuest XGBoost videos** (YouTube) - Best visual explanations
2. **Kaggle XGBoost tutorial** - Hands-on with real data
3. **Machine Learning Mastery** - Practical Python examples

### Key Concepts to Learn

1. **Gradient Boosting** - How trees are built sequentially
2. **Loss Functions** - Binary log loss for classification
3. **Regularization** - L1/L2 to prevent overfitting
4. **Cross-Validation** - Better than single train/test split
5. **Hyperparameter Tuning** - GridSearchCV, Optuna

---

## Learning More: Sports Betting ML

### Books
- "Trading Bases" by Joe Peta
- "Weighing the Odds in Sports Betting" by King Yao

### Concepts
1. **Closing Line Value (CLV)** - Did you beat the closing line?
2. **Kelly Criterion** - Optimal bet sizing
3. **Expected Value (EV)** - Long-term profitability
4. **Sharp vs Square** - Professional vs recreational bettors

### Data Considerations
- **No leakage** - Never use future data
- **Chronological validation** - Always split by time
- **Feature engineering** - Rolling stats, not season totals
- **Market efficiency** - Lines are set by smart people

---

## Improving the Model

### Ideas to Try

1. **Add more features**
   - Rest days (from `int_cfb__rest_schedule`)
   - Line movement (from `fct_cfb__line_movement`)
   - Home/away splits
   - Weather data

2. **Different models**
   - LightGBM (often faster)
   - Neural networks (for sequence data)
   - Ensemble of multiple models

3. **Hyperparameter tuning**
   ```python
   from sklearn.model_selection import GridSearchCV

   param_grid = {
       'max_depth': [3, 4, 5, 6],
       'n_estimators': [50, 100, 200],
       'learning_rate': [0.05, 0.1, 0.2]
   }
   ```

4. **Better validation**
   - Time-series cross-validation
   - Walk-forward validation
   - Out-of-season testing

5. **Calibration**
   - Are 60% predictions actually winning 60%?
   - Use `CalibratedClassifierCV`

---

## Running the Script

```bash
# From project root
cd C:\Users\paper\Desktop\Spread_Eagle

# Activate virtual environment
.\venv\Scripts\activate

# Run predictions
python -m spread_eagle.ml.predict_bowl_games
```

### Required Packages

```
pip install xgboost scikit-learn pandas numpy python-dotenv psycopg2-binary
```

---

## File Structure

```
spread_eagle/ml/
├── __init__.py
├── predict_bowl_games.py    # This script
├── train_teaser_model.py    # Teaser-specific model
├── train_matchup_model.py   # Alternative approach
└── ML_LEARNING_GUIDE.md     # This document
```

---

*Happy learning! The best way to improve is to experiment.*
