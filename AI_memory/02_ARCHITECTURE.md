# ARCHITECTURE — Spread Eagle

## 1) High-level goals (architecture-driven)
- Fully automated daily runs (initially for CBB)
- Cost-aware and simple first, scalable later
- Reproducible pipelines: raw → warehouse → dbt marts → predictions → app
- Clear separation: ingestion vs transforms vs modeling vs LLM content

---

## 2) End-to-end system flow (canonical)

### A) Ingestion (Python scripts)
- Pull raw data for:
  - schedules/games
  - team/player stats (as available)
  - sportsbook lines/odds (provider-specific)
- Write raw data to:
  - Postgres (raw tables) and/or S3 (raw JSON/CSV) depending on current setup
- Primary objective: completeness + timestamping, minimal transformation

**Rule:** ingestion scripts do not “massage” data beyond basic normalization.

---

### B) Storage (source of truth)
**Current:**
- AWS RDS Postgres holds ingested data

**Optional / recommended over time:**
- S3 raw landing (immutable) for replay/backfills

**Rule:** raw is never overwritten without a trace; use snapshot/date partitioning.

---

### C) Transform (dbt)
- dbt builds a clean semantic layer:
  - staging (`stg_*`): cleaned and typed
  - intermediate (`int_*`): joins, derived fields
  - facts (`fct_*`): analytics-ready
  - features (`feat_*`): ML and scoring-ready tables

**Rule:** anything needed for UI cards should ideally come from dbt tables so the UI is consistent.

---

### D) Modeling (Python)
- Uses feature tables to compute:
  - probability outputs (spread/total/moneyline)
  - teaser-adjusted probabilities (initially baseline/rules, later ML)
  - confidence buckets + calibration checks

Outputs written back to warehouse:
- `pred__*` tables, versioned by run timestamp and model version

**Rule:** the model consumes features; it does not re-implement feature logic.

---

### E) LLM TL;DR (RAG)
- Generates fun, readable summaries per game:
  - grounded in retrieved facts (RAG) from dbt outputs + curated notes
  - style: barstool-adjacent, entertaining, no guarantees
- Output is stored as **content**, not truth:
  - `content__tldr` table (or similar)

**Rule:** LLM text never becomes a numeric input to models unless explicitly designed and tested.

---

### F) App/API
- Displays sports tabs → daily slate → game detail
- Game detail renders 4–5 cards:
  1) Game context
  2) Betting snapshot
  3) TL;DR (LLM)
  4) Variance/risk profile
  5) (later) Deeper insights/probabilities

The app is a consumer of tables, not a computation layer.

---

## 3) Execution environment (where things run)

### Current (cost-aware)
- Daily orchestration runs on personal laptop:
  - Airflow (local) OR cron + Makefile-like scripts
- Connects to AWS RDS for reads/writes
- dbt runs locally against RDS target
- model + TL;DR generation runs locally and writes results to RDS

### Later (scale)
- Orchestration moved to cloud:
  - MWAA / ECS / Lambda / GitHub Actions / simple scheduled job
- Raw landing on S3 (recommended)
- Warehouse stays Postgres initially; optionally expand to analytics warehouse later

**Rule:** keep current architecture compatible with a “lift to cloud scheduler” later (no hard laptop-only assumptions).

---

## 4) Daily pipeline (canonical schedule)
A single "daily refresh" should:
1) ingest today's games + updated lines
2) ingest last results (yesterday) and any late updates
3) run dbt (stg → feat)
4) run modeling/prediction generation
5) run TL;DR generation
6) publish/serve results

---

## 5) Data contracts (interfaces between layers)

### Ingestion → dbt
- raw tables must include:
  - `source`
  - `pulled_at` timestamp
  - stable identifiers (game_id, team_id, etc.)

### dbt → modeling
- feature tables must:
  - declare grain explicitly
  - be deterministic for a given “as_of_date” and “line snapshot”
  - include label fields for training sets (where applicable)

### modeling → app
- `pred__*` tables must include:
  - model_version
  - trained_at
  - run_id or scored_at timestamp
  - inputs used (line snapshot reference)

### dbt/app → LLM
- RAG context should be built from:
  - game context metrics
  - betting snapshot
  - variance profile
  - any special notes
- Include citations/fields in context so summaries stay factual

---

## 6) Non-goals (architecture)
- No streaming or real-time infra for MVP
- No Kubernetes
- No complex event-driven architecture
- No multi-region or HA requirements initially

---

## 7) Architecture invariants (do not break)
- Raw data is replayable (or becomes replayable via S3 later)
- dbt is the single transform truth layer
- models are versioned and outputs are reproducible
- LLM content is clearly separated from numeric truth
