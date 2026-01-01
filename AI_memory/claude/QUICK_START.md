# QUICK START - Read This First

**For Claude instances starting a new session with this project.**

---

## What To Do First

1. Read this file completely
2. Read `PROJECT_OVERVIEW.md` for the big picture
3. Read `CURRENT_STATE.md` for where we left off
4. Check `SESSION_JOURNAL.md` for recent context
5. Ask the user what they want to work on today

---

## Project In One Sentence

**Spread Eagle** is an AI-driven sports betting analytics platform that ingests college football/basketball data, transforms it with dbt, trains ML models to predict ATS outcomes, and displays predictions in a Next.js dashboard.

---

## Tech Stack (Memorize This)

| Layer | Technology | Location |
|-------|------------|----------|
| Data Ingestion | Python + CFBD API | `spread_eagle/ingest/` |
| Database | PostgreSQL (AWS RDS) | Remote |
| Transformation | dbt | `dbt_transform/` |
| ML Models | XGBoost, scikit-learn | `spread_eagle/ml/` |
| Backend API | FastAPI | `spread_eagle/api/` |
| Frontend | Next.js 16 + React 19 | `ui/` |
| Orchestration | Airflow | `dags/` |
| Infrastructure | Terraform (AWS) | `infra/` |

---

## Key Folders

```
Spread_Eagle/
├── spread_eagle/      # Python package (API, ingest, ML)
├── dbt_transform/     # dbt models (staging → intermediate → marts)
├── ui/                # Next.js frontend
├── AI_memory/         # This folder - context for AI sessions
└── .env               # Database credentials (don't commit)
```

---

## Database Connection

```
Host: spread-eagle-db.cbwyw8ky62xm.us-east-2.rds.amazonaws.com
Port: 5432
DB: postgres
User: postgres
```

Credentials in `.env` file at project root.

---

## Common Commands

```bash
# Activate Python environment
cd C:\Users\paper\Desktop\Spread_Eagle
.\venv\Scripts\activate

# Run dbt models
cd dbt_transform
dbt run

# Run ML predictions
python -m spread_eagle.ml.predict_bowl_games

# Start frontend
cd ui
npm run dev
```

---

## Current Schemas in Postgres

| Schema | Purpose |
|--------|---------|
| `cfb` | Raw college football data |
| `cbb` | Raw college basketball data |
| `staging_cfb` | dbt staging views |
| `intermediate_cfb` | dbt intermediate tables |
| `marts_cfb` | dbt final tables (ML queries these) |

---

## User Preferences (Important!)

- Prefers hands-on, educational approach
- Wants to understand WHY, not just WHAT
- Learning dbt, XGBoost, data engineering
- Building portfolio project to showcase skills
- Wants clean, professional code structure

---

## After Reading This

1. Skim `PROJECT_OVERVIEW.md` for architecture details
2. Read `CURRENT_STATE.md` carefully - this is where we are NOW
3. Check latest entry in `SESSION_JOURNAL.md`
4. Greet user and ask what they want to tackle

**Don't make assumptions. Ask if unclear.**
