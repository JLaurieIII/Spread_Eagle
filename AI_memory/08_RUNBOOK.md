# RUNBOOK — Spread Eagle

## 1) Purpose of this file (operations-driven)
- Define how to run the system end-to-end without guesswork
- Provide a single reference for setup, execution, and recovery
- Reduce downtime caused by “how do I run this again?”
- Make failures diagnosable and repeatable
- Enable future migration to cloud schedulers with minimal changes

**Rule:** If it’s operationally important, it belongs here.

---

## 2) Supported execution modes (canonical)

### Local development
- Python virtual environment
- dbt running locally
- Airflow (local) OR cron-based scheduling
- Connects to AWS RDS Postgres

### Future cloud execution (not MVP)
- Same commands and entrypoints
- Different scheduler (MWAA / ECS / GitHub Actions)
- No logic changes, only environment changes

---

## 3) Environment setup (minimum viable)

### Python
- Create and activate virtual environment
- Install dependencies via `requirements.txt`
- Verify Python version compatibility

### Environment variables
Required:
- Database connection credentials
- Any sportsbook API keys
- Any LLM API keys
- Environment identifier (dev/local)

**Rule:** No secrets hardcoded in scripts or configs.

---

## 4) dbt setup and execution

### Configuration
- Ensure `profiles.yml` points to correct Postgres target
- Confirm schema and database names
- Verify dbt version compatibility

### Core commands
- `dbt debug` → validate connection
- `dbt run` → execute models
- `dbt test` → validate assumptions
- `dbt ls` → list available models

### Execution order
1. staging models
2. intermediate models
3. fact tables
4. feature tables
5. UI summary tables

**Rule:** dbt must run clean before modeling or UI validation.

---

## 5) Daily pipeline execution (canonical)

A full daily refresh consists of:

1. Ingest today’s games and updated lines
2. Ingest final results for completed games
3. Run dbt transformations (stg → feat)
4. Generate model predictions
5. Generate LLM TL;DR content
6. Validate outputs exist for all games
7. Publish results for UI consumption

This should be runnable via **one command or one DAG**.

---

## 6) Orchestration specifics

### Current (local-first)
- Single entrypoint script (e.g., `run_daily.py`)
- Airflow DAG OR cron triggers this script
- Script handles ordering and failure propagation

### Failure behavior
- Fail fast
- Log errors clearly
- Do not partially publish results

**Rule:** Silent failures are unacceptable.

---

## 7) Validation and sanity checks

After each daily run, confirm:
- All scheduled games exist in `fct__game`
- Market snapshots exist for each game
- Feature tables populated with no unexpected nulls
- Prediction tables populated with correct `model_version`
- TL;DR content exists for each game

If any check fails, the run is considered invalid.

---

## 8) Common failure scenarios and responses

### dbt models ran but tables not visible
- Verify target schema
- Confirm materialization type
- Ensure correct database connection
- Run `dbt run -v` for verbose output

### Missing games or lines
- Check ingestion logs
- Verify source availability
- Confirm date filters and timezones

### Model outputs missing or empty
- Verify feature table population
- Check model input filters
- Confirm model execution step ran

### TL;DR content missing
- Check LLM API availability
- Validate RAG context payload
- Ensure content table writes are not conditional

---

## 9) Backfills and re-runs

### Backfill rules
- Raw data first
- Then dbt transforms
- Then modeling
- Then content generation

### Re-run safety
- Scripts must be idempotent
- Re-runs should not corrupt historical data
- All writes must be traceable by timestamp or run_id

---

## 10) Logging and observability

Minimum logging per run:
- Run start and end time
- Record counts ingested
- dbt run status
- Model version and output counts
- LLM generation status

Logs should make it obvious where a failure occurred.

---

## 11) Recovery procedures

If a run fails:
1. Identify failing step
2. Fix root cause
3. Re-run from the earliest affected step
4. Validate downstream tables
5. Confirm UI-ready outputs

Never patch production data manually without documenting it.

---

## 12) Operational invariants (do not break)

- The system must be runnable end-to-end by one person
- Daily runs must be deterministic for a given date
- Failures must be loud and actionable
- Manual intervention should be rare and documented
- Operations should never depend on tribal knowledge
