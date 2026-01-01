# PROJECT OVERVIEW - Spread Eagle

## Vision

Build an AI-powered sports betting analytics platform that provides quantitative, data-driven insights for college football and basketball betting - specifically focused on spread (ATS) and totals (O/U) analysis.

**Unique Value Proposition:** Unlike typical betting sites, Spread Eagle gives you the "why" behind each pick - showing rolling performance, variance profiles, and model confidence rather than just picks.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
│  CFBD API (CFB)  |  CollegeBasketballData API (CBB)             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION LAYER                              │
│  Python scripts pull data → Load to PostgreSQL (AWS RDS)         │
│  Location: spread_eagle/ingest/cfb/ and /cbb/                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TRANSFORMATION LAYER (dbt)                     │
│                                                                  │
│  STAGING (views)           INTERMEDIATE (tables)                 │
│  ├─ stg_cfb__games         ├─ int_cfb__game_team_lines          │
│  ├─ stg_cfb__betting_lines ├─ int_cfb__team_rolling_form        │
│  └─ stg_cfb__teams         └─ int_cfb__rest_schedule            │
│                                                                  │
│  MARTS (tables) ─────────────────────────────────────────────   │
│  ├─ fct_cfb__matchup_snapshot    ← ML training data             │
│  ├─ fct_cfb__upcoming_predictions ← Upcoming games               │
│  ├─ fct_cfb__home_away_splits                                    │
│  └─ fct_cfb__line_movement                                       │
│                                                                  │
│  Location: dbt_transform/models/                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ML LAYER                                    │
│                                                                  │
│  Training: Historical games from fct_cfb__matchup_snapshot       │
│  Features: Rolling ATS margins, cover rates, win rates, deltas   │
│  Model: XGBoost classifier (predict cover probability)           │
│  Scoring: Apply to fct_cfb__upcoming_predictions                 │
│                                                                  │
│  Location: spread_eagle/ml/                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│                                                                  │
│  Backend: FastAPI (spread_eagle/api/)                            │
│  Frontend: Next.js 16 + React 19 (ui/)                           │
│                                                                  │
│  Pages:                                                          │
│  ├─ /              → Game detail dashboard (flag animation)      │
│  └─ /predictions   → Bowl game picks list                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Model (The "10 Views" Plan)

### Foundation
1. **int_cfb__game_team_lines** - Core table, 1 row per team per game, all ATS/OU calculations

### Rolling Features
2. **int_cfb__team_rolling_form** - Rolling avg/std of margins (last 3/5/10/20 games)
3. **int_cfb__team_margin_sequence** - Array of last N margins (for sequence models)

### Context Features
4. **fct_cfb__matchup_snapshot** - ML-ready: team features + opponent features joined
5. **fct_cfb__home_away_splits** - Home vs away performance splits
6. **int_cfb__rest_schedule** - Days rest, bye weeks, travel situations
7. **fct_cfb__line_movement** - Spread/total movement, steam moves

### Advanced (Future)
8. **fct_cfb__variance_profile** - Distribution shapes for teaser analysis
9. **fct_cfb__teaser_inputs** - Pre-computed teaser probabilities
10. **fct_cfb__bet_audit** - Track predictions vs outcomes

---

## Key Concepts

### ATS Margin
```
ATS Margin = (Team Score - Opponent Score) + Spread
```
- Positive = team covered
- Negative = team didn't cover
- Zero = push

### The Unpivot
Games come as 1 row per game. We transform to 1 row per TEAM per game:
- Home team gets the spread as-is
- Away team gets the spread flipped (×-1)

### No Future Leakage
All rolling calculations use:
```sql
ROWS BETWEEN N PRECEDING AND 1 PRECEDING
```
This ensures we only use data from BEFORE the current game.

---

## File Structure

```
Spread_Eagle/
├── spread_eagle/           # Python package
│   ├── api/               # FastAPI backend
│   ├── ingest/            # Data ingestion scripts
│   │   ├── cfb/          # College football
│   │   └── cbb/          # College basketball
│   ├── ml/                # Machine learning
│   │   ├── predict_bowl_games.py
│   │   └── ML_LEARNING_GUIDE.md
│   ├── core/              # Database models, schemas
│   └── config/            # Settings
│
├── dbt_transform/          # dbt project
│   ├── models/
│   │   ├── staging/cfb/   # Source → clean views
│   │   ├── intermediate/cfb/  # Business logic
│   │   └── marts/cfb/     # ML-ready tables
│   ├── macros/            # Custom schema naming
│   └── DBT_LEARNING_GUIDE.md
│
├── ui/                     # Next.js frontend
│   ├── app/
│   │   ├── page.tsx       # Main dashboard
│   │   ├── predictions/   # Bowl picks page
│   │   └── api/           # API routes
│   └── components/
│
├── AI_memory/              # Context for AI sessions
│   └── claude/
│
├── dags/                   # Airflow DAGs
├── infra/                  # Terraform
├── venv/                   # Python 3.12 virtual environment
├── .env                    # Credentials (not in git)
└── requirements.txt
```

---

## Learning Resources Created

1. `dbt_transform/DBT_LEARNING_GUIDE.md` - dbt best practices, layer cake, commands
2. `spread_eagle/ml/ML_LEARNING_GUIDE.md` - XGBoost explanation, feature engineering

---

## Future Roadmap

1. **CBB Models** - Replicate CFB structure for college basketball
2. **Live Scoring** - Real-time prediction updates
3. **Backtesting** - Historical accuracy tracking
4. **Teaser Analysis** - Probability adjustments for teased lines
5. **User Accounts** - Save picks, track personal ROI
6. **Alerts** - Notify on high-confidence plays
