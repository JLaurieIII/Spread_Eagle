# Environment Switching Guide

## Current Setup: LOCAL

Your development environment now runs entirely on your local machine.

---

## Quick Switch Commands

### Switch to LOCAL (current)
```bash
# Already done - no action needed
```

### Switch to AWS
```bash
# 1. Copy AWS settings to .env
copy .env.aws .env

# 2. Update dbt profiles.yml target
# In C:\Users\paper\.dbt\profiles.yml, change:
#   target: local
# to:
#   target: aws
```

---

## What Each Config Controls

| Component | Config File | Local Setting | AWS Setting |
|-----------|-------------|---------------|-------------|
| Python/Ingest | `.env` | `DB_HOST=localhost` | `DB_HOST=spread-eagle-db...rds.amazonaws.com` |
| FastAPI | `.env` | Same as above | Same as above |
| dbt | `~/.dbt/profiles.yml` | `target: local` | `target: aws` |

---

## Environment Files

| File | Purpose |
|------|---------|
| `.env` | **Active config** - Python/FastAPI reads this |
| `.env.local` | Backup of local settings |
| `.env.aws` | Backup of AWS settings |
| `~/.dbt/profiles.yml` | dbt config with both `local` and `aws` targets |

---

## Workflow: Local Development → AWS Push

1. **Develop locally**
   - Run ingest scripts (writes to local PostgreSQL)
   - Run dbt (transforms data locally)
   - Test API and frontend

2. **When ready to push to AWS**
   - Option A: Run `scripts/sync_local_to_aws.bat` (TODO: create this)
   - Option B: Switch to AWS config and run ingest/dbt again

---

## Database Details

| Environment | Host | Database | Port |
|-------------|------|----------|------|
| Local | `localhost` | `spread_eagle` | 5432 |
| AWS RDS | `spread-eagle-db.cbwyw8ky62xm.us-east-2.rds.amazonaws.com` | `postgres` | 5432 |

Both use:
- User: `postgres`
- Password: `Sport4788!`

---

## Running dbt

Always use the Python 3.12 venv (Python 3.14 has compatibility issues):

```bash
cd dbt_transform
.venv312\Scripts\dbt run
.venv312\Scripts\dbt test
```
