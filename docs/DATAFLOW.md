# Data Flow Model

This is the end-to-end view of how data moves through Spread Eagle.

## Sources
- **CollegeFootballData API (CFB)** — teams, games, lines.
- **CollegeBasketballData API (CBB)** — conferences, venues, teams, games, lines, team stats, player stats.
- **ESPN Scoreboard (CBB)** — upcoming games/lines for daily scoring (`ml/score_upcoming.py`).

## Landing & Raw
- **CFB → Postgres**: `spread_eagle/scripts/ingestion.py` pulls directly into tables (`teams`, `games`, `betting_lines`, `game_events`, `predictions`).
- **CBB → Files (raw)**: `spread_eagle/ingest/cbb/run_full_load.py` pulls each endpoint and writes JSON/CSV/Parquet under `data/cbb/raw/<dataset>/`. Optional S3 upload to `spread-eagle/cbb/raw/*`.

## Staging / Warehouse
- Postgres is the system of record.
- For CBB, raw CSV/Parquet can be bulk-loaded into Postgres using the mappings in `spread_eagle/config/table_mappings.py` (see `data/cbb/ddl/*.sql` and `spread_eagle/ingest/load_csv_debug.py` for helpers).

## Transform (dbt)
- Project: `dbt_transform/` (target schema e.g., `dbt_dev`).
- Key marts:
  - `fct_cbb_teaser_spread_dataset`: one row per team-game with leakage-safe windowed features (spread/total behavior, trend state, market profile, tail risk) and teaser outcome labels.
  - `fct_cbb_teaser_matchup_dataset`: one row per game with home/away features, combined matchup variance metrics, and parlay-style teaser labels.
- All features are computed with `ROWS BETWEEN N PRECEDING AND 1 PRECEDING` to avoid future leakage.

## Modeling
- **CFB Brain** (`spread_eagle/core/brain.py`):
  - Trains RandomForest on historical `games` table (completed games).
  - At inference, computes rolling averages for both teams’ last 5 games; applies qualitative adjustments from `game_events` (opt-outs, coaching changes).
  - Model artifact: `spread_eagle_model.pkl` (local path).
- **CBB Teaser Models** (`ml/`):
  - `train_teaser_model.py`: team-level teaser win classifier from `fct_cbb_teaser_spread_dataset`.
  - `train_matchup_model.py`: game-level parlay success classifier from `fct_cbb_teaser_matchup_dataset`.
  - `score_upcoming.py`: scores upcoming games using latest features + ESPN lines.
  - Models are XGBoost classifiers; features are leakage-safe, derived from dbt marts.

## Serving
- **API (FastAPI)**:
  - `GET /health` — status probe.
  - `GET /games` — list games from Postgres (filters: season, week).
  - `GET /predict/{game_id}` — runs CFB brain, returns spread prediction with qualitative adjustments.
- **Frontend (Next.js)**:
  - `ui/app/page.tsx` currently uses mock payloads shaped to the intended API response; swap in real API calls later.

## Storage & Artifacts
- **Primary DB**: Postgres (RDS via Terraform in `infra/terraform/app`).
- **Files**: `data/<sport>/raw|processed` (gitignored). S3 bucket `spread-eagle` for CBB uploads.
- **Models**: Pickle artifacts (local); can be moved to `data/models/` or object storage.

## Ops quick start
- CFB ingest → `python spread_eagle/scripts/ingestion.py`
- CBB full ingest → `python -m spread_eagle.ingest.cbb.run_full_load`
- dbt → `dbt build --project-dir dbt_transform --target dev`
- Train CFB brain → `python spread_eagle/scripts/train_brain.py`
- Train/score CBB → `python ml/train_teaser_model.py`, `python ml/train_matchup_model.py`, `python ml/score_upcoming.py`



