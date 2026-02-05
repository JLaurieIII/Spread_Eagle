# Spread Eagle Development Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRODUCTION FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [CBB API] ──► [Airflow Ingest] ──► [RDS PostgreSQL] ──► [dbt] │
│                                            │                    │
│                                            ▼                    │
│                                   [FastAPI :8000]               │
│                                            │                    │
│                                            ▼                    │
│                                   [Next.js UI :3000]            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Port Assignments

| Service | Port | Description |
|---------|------|-------------|
| **FastAPI** | 8000 | Backend API - serves dashboard data |
| **Next.js UI** | 3000 | Frontend - React dashboard |
| **RDS PostgreSQL** | 5432 | AWS database (production) |
| **Airflow Web** | 8080 | DAG management UI |

## Configuration Files

| File | Purpose |
|------|---------|
| `.env` | API database connection (points to RDS) |
| `ui/.env.local` | UI API endpoint (must match API port) |
| `~/.dbt/profiles.yml` | dbt database targets |
| `airflow/dags/cbb_daily_pipeline.py` | Ingest + transform pipeline |

## Quick Start

```powershell
# Check what's running
.\dev.ps1 status

# Start everything
.\dev.ps1 start

# Stop everything
.\dev.ps1 stop

# Kill all node/python processes
.\dev.ps1 kill
```

## Database: RDS Only

**There is NO local PostgreSQL for this project.** All data flows through AWS RDS:

- Host: `spread-eagle-db.cbwyw8ky62xm.us-east-2.rds.amazonaws.com`
- Database: `postgres`
- Schema: `cbb` (source), `marts_cbb` (transformed)

## Daily Pipeline (Airflow)

The `cbb_daily_pipeline` DAG runs at 8 AM daily:

1. **Ingest**: Pull 7-day rolling window from CBB API
2. **Upsert**: Load to RDS PostgreSQL
3. **dbt**: Transform into dashboard marts

To run manually:
```bash
# Trigger from Airflow UI at localhost:8080
# Or run dbt directly:
docker exec airflow-airflow-scheduler-1 bash -c "cd /opt/airflow/dbt_transform && dbt run --select tag:cbb --target aws"
```

## Common Issues

### UI shows "TBD" for betting lines
1. Check `ui/.env.local` points to correct API port (8000)
2. Hard refresh browser (Ctrl+Shift+R)
3. Verify API is running: `curl http://localhost:8000/cbb/dashboard?date=2026-01-28`

### Games on wrong date
- Timezone issue: dbt converts UTC to Eastern time
- Check `fct_cbb__game_dashboard.sql` uses `AT TIME ZONE 'America/New_York'`

### Port already in use
```powershell
# Find what's using a port
netstat -ano | findstr ":8000"

# Kill by PID
taskkill /F /PID <pid>
```
