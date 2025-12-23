# Spread Eagle
College football & basketball data/ML playground with a FastAPI backend and a Next.js UI.

## Repository layout
- `spread_eagle/` – backend code: API, ingestion scripts, models, database layer.
- `ui/` – Next.js app for the frontend.
- `data/` – raw and processed datasets (large; kept out of git by default).
- `models/` – trained model artifacts (e.g., `cfb_model.pkl`).
- `scripts/` – helper scripts for ingestion/training.

## Prerequisites
- Python 3.11+ and `pip`
- Node 18+ and `npm`
- PostgreSQL accessible via `DATABASE_URL`
- API keys: CFBD (`CFB_API_KEY`) and CollegeBasketballData (`CBB_API_KEY`)

## Backend setup (FastAPI)
```powershell
cd C:\Users\paper\Desktop\Spread_Eagle
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

Create `.env` in the repo root:
```
ENV=dev
DATABASE_URL=postgresql://user:pass@localhost:5432/spread_eagle
CFB_API_KEY=your_cfbd_key
CBB_API_KEY=your_cbb_key
```

Initialize the database (optional helper):
```powershell
python spread_eagle/scripts/setup_db.py
```

Run the API:
```powershell
uvicorn spread_eagle.api.main:app --reload --port 8000
```

## Data ingestion
- College football: `python spread_eagle/scripts/ingestion.py` (uses `CFB_API_KEY`; writes to Postgres).
- College basketball: `python spread_eagle/ingest/cbb/pull_games_full.py` (uses `CBB_API_KEY`; writes JSON near the script).
- Additional bulk pulls live under `spread_eagle/ingest/cfb/` (drives, games, lines).

## Frontend (Next.js)
```powershell
cd C:\Users\paper\Desktop\Spread_Eagle\ui
npm install
npm run dev
```
Open http://localhost:3000. Point any API calls at the FastAPI server (default http://localhost:8000).

## Git/GitHub quickstart
1) Create a new GitHub repo (e.g., `spread-eagle`).  
2) From repo root: `git init`  
3) Optionally set your user info: `git config user.name "Your Name"` and `git config user.email "you@example.com"`.  
4) Stage and commit: `git add .` then `git commit -m "Initial commit"`.  
5) Add remote: `git remote add origin https://github.com/<you>/spread-eagle.git`  
6) Push: `git branch -M main` then `git push -u origin main`

## Development tips
- Keep data dumps and virtualenvs out of git (see `.gitignore`).
- Run backend and frontend in separate terminals.
- Use branches + PRs for changes once on GitHub.