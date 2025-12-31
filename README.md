# Spread Eagle

<p align="center">
  <img src="docs/logo.jpeg" width="220" alt="Spread Eagle logo" />
</p>

<p align="center">
  <img src="docs/Spread_Eagle_Architecture.png" width="900" alt="Spread Eagle architecture overview">
</p>

> AI-driven college football & basketball insights — ingestion → dbt → ML → FastAPI → Next.js.

College football & basketball data / ML playground with a FastAPI backend and a Next.js UI. Includes ingestion pipelines, dbt transforms, teaser/variance ML models, and a mock-driven frontend.

## At a glance
- **Backend:** FastAPI + SQLAlchemy over Postgres (`spread_eagle/api`, `core`).
- **Data ingest:** CFBD + CollegeBasketballData clients; CFB writes straight to Postgres, CBB saves raw JSON/CSV/Parquet (optional S3).
- **Transform:** dbt project (`dbt_transform/`) builds leakage-safe marts for ML.
- **ML:** RandomForest “brain” for CFB; XGBoost teaser models for CBB.
- **Frontend:** Next.js app (`ui/`) currently using mock payloads shaped to the intended API response.

## Setup
```powershell
cd C:\Users\paper\Desktop\Spread_Eagle
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

Create `.env` in repo root:
```
ENV=dev
DATABASE_URL=postgresql://user:pass@localhost:5432/spread_eagle
CFB_API_KEY=your_cfbd_key
CBB_API_KEY=your_cbb_key
```

## Running services
- **API (dev):**
  ```powershell
  uvicorn spread_eagle.api.main:app --reload --port 8000
  ```
- **Frontend (dev):**
  ```powershell
  cd ui
  npm install
  npm run dev
  ```
  Open http://localhost:3000 (point calls at http://localhost:8000).

## Data flow (high level)
1) **Ingest**
   - CFB → `spread_eagle/scripts/ingestion.py` pulls teams/games from CFBD, writes to Postgres tables (`teams`, `games`, `betting_lines`, etc.).
   - CBB → `spread_eagle/ingest/cbb/run_full_load.py` pulls conferences/venues/teams/games/lines/stats, saves under `data/cbb/raw/*` (CSV/Parquet/JSON) and can upload to S3 `spread-eagle`.
2) **Transform**
   - dbt (`dbt_transform/`) materializes marts such as `fct_cbb_teaser_spread_dataset` (team-game features + teaser labels) and `fct_cbb_teaser_matchup_dataset` (game-level combined features).
3) **Model**
   - CFB: `SpreadEagleBrain` trains a RandomForest on `games` table and adjusts predictions with `game_events`.
   - CBB: XGBoost classifiers (`ml/train_teaser_model.py`, `ml/train_matchup_model.py`) read dbt marts; `ml/score_upcoming.py` scores near-term slates.
4) **Serve**
   - FastAPI exposes `/health`, `/games`, `/predict/{game_id}`.
   - Next.js UI consumes the intended JSON payload shape (currently mocked in `ui/app/page.tsx`).

## Common commands
- **CFB ingest to Postgres**
  ```powershell
  python spread_eagle/scripts/ingestion.py
  ```
- **CBB full ingest (raw files)**
  ```powershell
  python -m spread_eagle.ingest.cbb.run_full_load
  ```
- **dbt (from repo root)**
  ```powershell
  dbt deps   --project-dir dbt_transform
  dbt build  --project-dir dbt_transform --target dev
  ```
- **Train CFB brain**
  ```powershell
  python spread_eagle/scripts/train_brain.py   # or call SpreadEagleBrain().train()
  ```
- **Train/score CBB teaser models**
  ```powershell
  python ml/train_teaser_model.py
  python ml/train_matchup_model.py
  python ml/score_upcoming.py
  ```

## API surface (current)
- `GET /health` → `{status:"ok"}`
- `GET /games?season=2024&week=1` → list of games from Postgres
- `GET /predict/{game_id}` → spread prediction with qualitative adjustments

## Directory guide
- `spread_eagle/` — backend (API, DB models, ingestion).
- `dbt_transform/` — dbt project for CBB feature/label marts.
- `ml/` — teaser and matchup models (CBB).
- `data/` — raw/processed dumps (not in git by default).
- `docs/` — generated diagrams and doc generators.
- `ui/` — Next.js frontend (mocked data today).

## Deploy / GitHub
- Terraform under `infra/terraform/app` provisions RDS + VPC + S3 (dev profile `spread-eagle-dev`).
- To publish updates to GitHub:
  ```powershell
  git status
  git add .
  git commit -m "Update docs and data flow"
  git push origin main
  ```

## Notes
- Keep `.env`, `data/`, and `.venv` out of git (see `.gitignore`).
- API keys are required for ingestion (CFB/CBB). Postgres must be reachable via `DATABASE_URL`.