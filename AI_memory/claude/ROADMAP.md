# ROADMAP - Spread Eagle Development Plan

## The Big Picture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SPREAD EAGLE VISION                              │
│                                                                          │
│   Find LOW VOLATILITY games → TEASE them → EXPLOIT the edge             │
│                                                                          │
│   Theory: Teams with consistent ATS margins (low std dev) are           │
│   safer teaser candidates. If a team covers by 7± 2 pts regularly,      │
│   teasing them 6-8 points creates high probability outcomes.            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation (COMPLETE)

- [x] Database setup (AWS RDS PostgreSQL)
- [x] CFB data ingestion pipeline
- [x] dbt project structure
- [x] CFB staging models
- [x] CFB intermediate models (foundation, rolling, rest)
- [x] CFB marts (matchup snapshot, upcoming predictions)
- [x] Basic XGBoost ATS predictor
- [x] Next.js frontend scaffold
- [x] AI memory system

---

## Phase 2: CBB Pipeline (NEXT)

### 2.1 Data Verification
- [ ] Verify CBB raw data exists in `cbb` schema
- [ ] Check data quality (nulls, date ranges, line coverage)
- [ ] Document CBB-specific quirks (conference tournaments, back-to-backs)

### 2.2 dbt Models for CBB
```
models/staging/cbb/
├── _cbb__sources.yml
├── stg_cbb__games.sql
├── stg_cbb__betting_lines.sql
└── stg_cbb__teams.sql

models/intermediate/cbb/
├── int_cbb__game_team_lines.sql      # Foundation
├── int_cbb__team_rolling_form.sql    # Rolling stats
└── int_cbb__rest_schedule.sql        # Back-to-backs critical in CBB

models/marts/cbb/
├── fct_cbb__matchup_snapshot.sql
├── fct_cbb__upcoming_predictions.sql
├── fct_cbb__variance_profile.sql     # KEY for teaser strategy
└── fct_cbb__teaser_candidates.sql    # Low volatility filter
```

### 2.3 CBB-Specific Considerations
| Factor | CFB | CBB |
|--------|-----|-----|
| Games per season | 12-15 | 30-35 |
| Rolling window | 5, 10 | 10, 20 |
| Back-to-backs | Rare | Common (key feature) |
| Conference tournaments | None | Yes (March) |
| Travel impact | Moderate | High |
| Sample size | Limited | Rich |

---

## Phase 3: Variance Profile & Teaser Strategy

### 3.1 The Teaser Thesis

**Teasers** adjust the spread in your favor (usually 6-7 points in basketball). The cost is reduced payout and you must parlay 2+ legs.

**The Edge:**
- Find teams with LOW ATS variance (consistent margins)
- These teams' outcomes cluster tightly around their mean
- Teasing them into that cluster = high probability

**Example:**
```
Team A: ATS margins last 20 games = [+3, +5, +2, +4, +6, +3, +5, ...]
        Mean: +4, Std Dev: 1.5 → LOW VOLATILITY → Good teaser candidate

Team B: ATS margins last 20 games = [-10, +15, +2, -8, +20, ...]
        Mean: +4, Std Dev: 12 → HIGH VOLATILITY → Bad teaser candidate
```

### 3.2 Variance Profile Model

```sql
-- fct_cbb__variance_profile.sql

Key columns:
- team_id
- ats_margin_mean_l20
- ats_margin_std_l20         -- THE KEY METRIC
- ats_margin_skew_l20        -- Distribution shape
- pct_games_within_7_pts     -- How often within teaser range
- pct_blowouts_l20           -- Games with |margin| > 15
- consistency_score          -- Composite metric
```

### 3.3 Teaser Candidate Model

```sql
-- fct_cbb__teaser_candidates.sql

Filters:
- ats_margin_std_l20 < 8     -- Low volatility
- games_played >= 15         -- Sufficient sample
- pct_games_within_7_pts > 0.6  -- Consistent margins

Output:
- team_id, opponent_id
- current_spread
- teased_spread (spread + 6)
- p_cover_standard           -- Model probability at current spread
- p_cover_teased             -- Model probability at teased spread
- edge_score                 -- Expected value indicator
```

---

## Phase 4: Airflow Orchestration

### 4.1 DAG Structure

```python
# dags/daily_pipeline.py

Schedule: 6:00 AM ET daily

Tasks:
1. ingest_cfb_games        → Pull new CFB data
2. ingest_cfb_lines        → Pull updated lines
3. ingest_cbb_games        → Pull new CBB data
4. ingest_cbb_lines        → Pull updated lines
5. dbt_run_staging         → Refresh staging views
6. dbt_run_intermediate    → Rebuild intermediate
7. dbt_run_marts           → Rebuild marts
8. run_ml_predictions      → Score upcoming games
9. notify_high_confidence  → Alert on strong plays
```

### 4.2 Files to Create

```
dags/
├── daily_pipeline.py       # Main orchestration
├── utils/
│   ├── db.py              # Database connections
│   └── notifications.py   # Slack/email alerts
└── config/
    └── schedules.py       # Cron expressions
```

### 4.3 Airflow Setup Steps

1. Install Airflow in venv
2. Initialize Airflow database
3. Configure connections (Postgres, APIs)
4. Create DAG file
5. Test locally
6. (Later) Deploy to cloud

---

## Phase 5: Enhanced ML Pipeline

### 5.1 Model Registry

```
spread_eagle/ml/
├── models/
│   ├── cfb_ats_v1.pkl         # Current XGBoost
│   ├── cbb_ats_v1.pkl         # CBB version
│   └── cbb_teaser_v1.pkl      # Teaser-specific model
├── training/
│   ├── train_ats_model.py
│   ├── train_teaser_model.py
│   └── hyperparameter_search.py
├── scoring/
│   ├── score_upcoming.py
│   └── backtest.py
└── evaluation/
    ├── metrics.py
    └── calibration.py
```

### 5.2 Feature Engineering Priorities

**For Teaser Model:**
1. `ats_margin_std_l20` - Volatility measure
2. `pct_games_within_teaser_range` - Historical teaser success
3. `opponent_volatility` - Other side's variance
4. `rest_differential` - Schedule advantage
5. `home_away_volatility_split` - Location-based variance

### 5.3 Model Evaluation

```
Metrics to track:
- Accuracy (% correct picks)
- Calibration (60% predictions win 60%?)
- ROI (profit/loss simulation)
- Closing Line Value (did we beat the close?)
```

---

## Phase 6: Frontend Evolution

### 6.1 Pages to Build

| Route | Purpose |
|-------|---------|
| `/` | Dashboard overview |
| `/predictions` | Today's picks (done) |
| `/predictions/cfb` | CFB specific |
| `/predictions/cbb` | CBB specific |
| `/teasers` | Teaser candidates |
| `/team/:id` | Team deep dive |
| `/backtest` | Historical performance |

### 6.2 Key Components

```
components/
├── predictions/
│   ├── PredictionCard.tsx
│   ├── ConfidenceMeter.tsx
│   └── SpreadDisplay.tsx
├── teasers/
│   ├── TeaserBuilder.tsx      # Build your teaser parlay
│   ├── VolatilityChart.tsx    # Visualize team variance
│   └── TeaserOddsCalc.tsx     # Calculate parlay odds
└── analytics/
    ├── MarginDistribution.tsx  # Histogram of margins
    └── RollingTrendChart.tsx   # ATS margin over time
```

---

## Priority Order

### This Week
1. [ ] Verify CBB raw data quality
2. [ ] Build CBB staging models
3. [ ] Build CBB intermediate models
4. [ ] Build `fct_cbb__variance_profile`

### Next Week
5. [ ] Build teaser candidate model
6. [ ] Train CBB ATS model
7. [ ] Train teaser-specific model
8. [ ] Setup Airflow locally

### Following Weeks
9. [ ] Backtest teaser strategy
10. [ ] Build teaser UI components
11. [ ] Add real-time line updates
12. [ ] Deploy to cloud

---

## Success Metrics

| Metric | Target |
|--------|--------|
| CBB ATS Accuracy | > 52% |
| Teaser Win Rate | > 70% |
| ROI (flat betting) | > 3% |
| Closing Line Value | Positive |
| Model Calibration | < 5% error |

---

## Open Questions

1. **Line source:** Are we getting opening lines for movement analysis?
2. **Live updates:** How often to refresh predictions?
3. **Teaser legs:** 2-team or 3-team teasers?
4. **Bankroll:** Kelly criterion or flat betting?
5. **Alerting:** Slack, email, or push notifications?
