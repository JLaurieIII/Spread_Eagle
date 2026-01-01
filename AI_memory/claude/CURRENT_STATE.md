# CURRENT STATE

**Last Updated:** 2026-01-01 @ ~8:00 PM EST

---

## What's Working

### Data Pipeline
- [x] Raw CFB data in PostgreSQL (seasons 2022-2025)
- [x] Betting lines for upcoming bowl games (2026-01-01 through 01-06)
- [x] dbt project initialized and configured
- [x] Custom schema macro for clean schema names

### dbt Models (CFB)
- [x] **Staging** (3 models) - `staging_cfb` schema
  - `stg_cfb__games`
  - `stg_cfb__betting_lines`
  - `stg_cfb__teams`

- [x] **Intermediate** (4 models) - `intermediate_cfb` schema
  - `int_cfb__game_team_lines` (FOUNDATION - 11,980 rows)
  - `int_cfb__team_rolling_form` (rolling stats)
  - `int_cfb__team_margin_sequence` (arrays - slow, 89s)
  - `int_cfb__rest_schedule` (rest days, bye weeks)

- [x] **Marts** (5 models) - `marts_cfb` schema
  - `fct_cfb__matchup_snapshot` (ML training data - 9,598 rows)
  - `fct_cfb__upcoming_predictions` (upcoming games - 24 rows)
  - `fct_cfb__home_away_splits`
  - `fct_cfb__line_movement`

### ML Pipeline
- [x] XGBoost classifier trained on historical data
- [x] Validation accuracy: ~52-55% (slight edge over baseline)
- [x] `predict_bowl_games.py` script working
- [x] Predictions generated for 12 bowl games

### Frontend
- [x] Next.js app structure in place
- [x] Main dashboard page with flag animation (`/`)
- [x] Predictions page created (`/predictions`)
- [x] API route for predictions (`/api/predictions`)

---

## What's NOT Working / Incomplete

### Known Issues
- [ ] Predictions page formatting is "off" (user noted)
- [ ] `int_cfb__team_margin_sequence` is slow (89s) - needs optimization
- [ ] Sequence arrays not properly limited to N elements

### Not Built Yet
- [ ] CBB models (basketball) - structure planned, not implemented
- [ ] Variance profile model (#8)
- [ ] Teaser inputs model (#9)
- [ ] Bet audit model (#10)
- [ ] FastAPI backend not connected to dbt models
- [ ] Live database queries in Next.js (currently using static data)

---

## Today's Bowl Games (2026-01-01)

| Game | Pick | Confidence | Rating |
|------|------|------------|--------|
| Miami @ Ohio State | Ohio State -9.5 | 60% | PLAY |
| Oregon @ Texas Tech | Oregon -2.5 | 53% | LEAN |
| Alabama @ Indiana | Indiana -7.0 | 57% | LEAN |

**Best Plays (60%+ confidence):**
1. Iowa +3.0 vs Vanderbilt (61%)
2. Ohio State -9.5 vs Miami (60%)
3. Wake Forest +2.8 vs Miss State (64%)

---

## Environment

- **Python:** 3.12.10 (in venv)
- **dbt:** 1.11.2
- **Node:** (check with `node -v`)
- **Working Directory:** `C:\Users\paper\Desktop\Spread_Eagle`

---

## Last Session Summary

**Date:** 2026-01-01

**What We Did:**
1. Moved `ml/` folder into `spread_eagle/` package
2. Initialized dbt from scratch
3. Built all CFB staging → intermediate → marts models
4. Created `fct_cfb__upcoming_predictions` for upcoming games
5. Built XGBoost prediction script
6. Generated predictions for bowl games
7. Created predictions page in Next.js frontend
8. Created this AI memory system

**User Learning Focus:**
- dbt best practices (layer cake, materializations)
- XGBoost basics
- Data engineering patterns

---

## Next Logical Steps

1. **Fix predictions page formatting** - UI cleanup
2. **Build CBB models** - Copy CFB patterns for basketball
3. **Connect real database to frontend** - Replace static predictions
4. **Optimize slow models** - `int_cfb__team_margin_sequence`
5. **Add remaining marts** - variance profile, teaser inputs, audit

---

## Quick Test Commands

```bash
# Verify dbt connection
cd C:\Users\paper\Desktop\Spread_Eagle\dbt_transform
dbt debug

# Rebuild all models
dbt run

# Run predictions
cd C:\Users\paper\Desktop\Spread_Eagle
python -m spread_eagle.ml.predict_bowl_games

# Start frontend
cd ui && npm run dev
```
