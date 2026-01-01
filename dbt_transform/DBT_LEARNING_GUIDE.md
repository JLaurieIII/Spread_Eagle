# dbt Learning Guide: Spread Eagle Analytics

This document covers everything we built and teaches dbt best practices.

---

## What is dbt?

**dbt (data build tool)** transforms data already in your warehouse using SQL.

```
Python (Extract/Load) -> Postgres (raw) -> dbt (Transform) -> Postgres (clean) -> ML/API
```

### Why dbt?

| Feature | Benefit |
|---------|---------|
| Version control | SQL in git, changes tracked |
| Dependencies | dbt knows Table A needs Table B |
| Testing | Built-in data quality tests |
| Documentation | Auto-generated lineage graphs |

---

## The Layer Cake

### Layer 1: Staging (stg_)

**Purpose:** 1:1 with source tables, light cleaning only.

- One staging model per source table
- Rename columns to snake_case
- Cast types properly
- NO business logic, NO joins
- **Materialization:** `view`

### Layer 2: Intermediate (int_)

**Purpose:** Business logic, joins, window functions.

- Can reference staging and other intermediate models
- This is where the magic happens
- **Materialization:** `view` or `table`

### Layer 3: Marts (fct_, dim_)

**Purpose:** Consumer-ready tables for ML, API, dashboards.

- `fct_` = Fact tables (events, measurements)
- `dim_` = Dimension tables (descriptive)
- **Materialization:** `table`

---

## Project Structure

```
dbt_transform/
├── dbt_project.yml
├── macros/
│   └── get_custom_schema.sql
├── models/
│   ├── staging/cfb/
│   │   ├── _cfb__sources.yml
│   │   ├── stg_cfb__games.sql
│   │   ├── stg_cfb__betting_lines.sql
│   │   └── stg_cfb__teams.sql
│   ├── intermediate/cfb/
│   │   ├── int_cfb__game_team_lines.sql
│   │   ├── int_cfb__team_rolling_form.sql
│   │   ├── int_cfb__team_margin_sequence.sql
│   │   └── int_cfb__rest_schedule.sql
│   └── marts/cfb/
│       ├── fct_cfb__matchup_snapshot.sql
│       ├── fct_cfb__home_away_splits.sql
│       └── fct_cfb__line_movement.sql
```

---

## Our 10-Model Architecture

| # | Model | Layer | Purpose |
|---|-------|-------|---------|
| 1 | int_cfb__game_team_lines | int | FOUNDATION - Unpivot to team-game grain |
| 2 | int_cfb__team_rolling_form | int | Rolling avg/std (last 3/5/10 games) |
| 3 | int_cfb__team_margin_sequence | int | Array of last N margins |
| 4 | fct_cfb__matchup_snapshot | mart | ML TABLE - Team + opponent features |
| 5 | fct_cfb__home_away_splits | mart | Home vs away performance |
| 6 | int_cfb__rest_schedule | int | Days rest, bye weeks |
| 7 | fct_cfb__line_movement | mart | Spread/total movement |
| 8-10 | (To build) | mart | Variance, teaser, audit |

---

## The Critical Unpivot

Games come as 1 row per game. We need 1 row per TEAM per game:

```sql
-- HOME team perspective
select
    home_id as team_id,
    spread as spread_close_for_team,
    (home_points - away_points) + spread as ats_margin

union all

-- AWAY team perspective (FLIP THE SPREAD!)
select
    away_id as team_id,
    -1 * spread as spread_close_for_team,
    (away_points - home_points) + (-1 * spread) as ats_margin
```

---

## No Future Leakage

When calculating rolling stats:

```sql
rows between 10 preceding and 1 preceding
```

This means: Look at 10 games BEFORE, excluding current game.

**Critical for ML** - cannot use future data to predict past!

---

## Key Commands

```bash
dbt debug          # Test connection
dbt compile        # Check SQL syntax
dbt run            # Build all models
dbt run --select staging.cfb     # Build folder
dbt run --select model_name+     # Model + downstream
dbt test           # Run data tests
dbt docs generate  # Build docs
dbt docs serve     # View in browser
```

---

## Extending to CBB

1. Create `models/staging/cbb/_cbb__sources.yml`
2. Copy CFB staging models, change cfb to cbb
3. Copy intermediate models
4. Copy mart models

### CBB Differences

| Aspect | CFB | CBB |
|--------|-----|-----|
| Games/season | 12-15 | 30-35 |
| Back-to-backs | Rare | Common |
| Rolling windows | 5, 10 | 10, 20 |

---

## Schemas Created

| Schema | Contents |
|--------|----------|
| staging_cfb | stg_cfb__* views |
| intermediate_cfb | int_cfb__* tables |
| marts_cfb | fct_cfb__* tables |

---

## Materializations

| Type | Use Case |
|------|----------|
| view | Staging (always fresh) |
| table | Heavy transforms, ML queries |
| incremental | Append-only, large data |
| ephemeral | Inline CTE, no object |

---

## Best Practices

- One model per file
- Sources in _sources.yml
- Staging as views
- Heavy transforms as tables
- Avoid correlated subqueries
- Comments for complex logic

---

*Created: 2025-01-01 | Project: Spread Eagle Analytics*
