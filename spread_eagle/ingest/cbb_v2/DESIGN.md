# CBB V2 Ingestion Pipeline - Design Document

## Overview

The CBB V2 pipeline is a complete rewrite of the College Basketball data ingestion system, designed for:
- **Single orchestrator entry point** for Airflow integration
- **Full and Incremental (CDC) loading modes**
- **Direct Postgres loading** with upsert logic
- **Dual output** to both files (JSON/CSV) and database

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     run_ingest.py                                │
│                 (Master Orchestrator)                            │
│                                                                  │
│  Usage: python -m spread_eagle.ingest.cbb_v2.run_ingest         │
│         --mode full|incremental                                  │
│         --start_year 2022 --end_year 2025                       │
│         --datasets games,lines,team_game_stats                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Individual Loaders                            │
├─────────────────────────────────────────────────────────────────┤
│  load_teams.py          │ Reference data (full only)            │
│  load_venues.py         │ Reference data (full only)            │
│  load_games.py          │ Games (full + incremental)            │
│  load_team_game_stats.py│ Per-game team stats (full + incr)     │
│  load_lines.py          │ Betting lines (full + incremental)    │
│  load_team_season_stats.py │ Team season aggregates (full+incr) │
│  load_player_season_stats.py │ Player season stats (full+incr)  │
│  load_game_players.py   │ Per-game player stats (full + incr)   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      common.py                                   │
│                  (Shared Utilities)                              │
├─────────────────────────────────────────────────────────────────┤
│  CBBAPIClient        │ API client with pagination & rate limit  │
│  upsert_dataframe()  │ Postgres upsert with conflict handling   │
│  ensure_schema_exists│ Schema creation                          │
│  flatten_json()      │ JSON normalization                       │
│  clean_column_names()│ Postgres-safe column naming              │
│  dedupe_records()    │ Record deduplication                     │
│  get_current_season()│ Season year calculation                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Full Load Mode (`--mode full`)

1. **Reference Data** (teams, venues)
   - Always full reload
   - Upserts all records (updates existing, inserts new)

2. **Transactional Data** (games, stats, lines)
   - Pulls data for specified year range (`--start_year` to `--end_year`)
   - Deduplicates within and across seasons
   - Upserts to database with primary key conflict handling

### Incremental/CDC Mode (`--mode incremental`)

1. **Reference Data** (teams, venues)
   - Still runs full reload (reference data changes rarely)

2. **Transactional Data**
   - Only pulls CURRENT SEASON data
   - Season is calculated as:
     - Nov-Dec: Next year's season (Nov 2024 = 2025 season)
     - Jan-Apr: Current year's season
     - May-Oct: Upcoming season
   - Upserts only new/changed records

---

## Database Schema

All data is loaded into the `cbb_raw` schema with the following tables:

| Table | Primary Key | Description |
|-------|-------------|-------------|
| `cbb_raw.teams` | `id` | Team reference data |
| `cbb_raw.venues` | `id` | Venue/arena reference data |
| `cbb_raw.games` | `id` | Game results and metadata |
| `cbb_raw.team_game_stats` | `(game_id, team_id)` | Per-game team box scores |
| `cbb_raw.lines` | `(game_id, provider)` | Betting lines by provider |
| `cbb_raw.team_season_stats` | `(season, team_id)` | Aggregated team stats |
| `cbb_raw.player_season_stats` | `(season, athlete_id)` | Aggregated player stats |
| `cbb_raw.game_players` | `(game_id, team_id, athlete_id)` | Per-game player stats |

---

## File Outputs

Each loader writes to `data/cbb/raw/`:

| Dataset | JSON Output | CSV Output |
|---------|-------------|------------|
| teams | `teams_v2.json` | `teams_v2.csv` |
| venues | `venues_v2.json` | `venues_v2.csv` |
| games | `games_{year}_v2.json` (per year) | `games_{start}_{end}_v2.csv` |
| team_game_stats | `team_game_stats_{year}_v2.json` | `team_game_stats_{start}_{end}_v2.csv` |
| lines | `lines_{year}_v2.json` | `lines_{start}_{end}_v2.csv` |
| team_season_stats | `team_season_stats_{year}_v2.json` | `team_season_stats_{start}_{end}_v2.csv` |
| player_season_stats | `player_season_stats_{year}_v2.json` | `player_season_stats_{start}_{end}_v2.csv` |
| game_players | `game_players_{year}_v2.json` | `game_players_{start}_{end}_v2.csv` |

---

## API Details

**Base URL**: `https://api.collegebasketballdata.com`

**Authentication**: Bearer token via `CBB_API_KEY` environment variable

**Endpoints Used**:
| Endpoint | Loader | Notes |
|----------|--------|-------|
| `/teams` | load_teams | No pagination needed |
| `/venues` | load_venues | No pagination needed |
| `/games` | load_games | Pagination, season/seasonType params |
| `/games/teams` | load_team_game_stats | Pagination, season/seasonType params |
| `/lines` | load_lines | Pagination, season/seasonType params |
| `/stats/team/season` | load_team_season_stats | Pagination, season param |
| `/stats/player/season` | load_player_season_stats | Pagination, season param |
| `/games/players` | load_game_players | Pagination, season/seasonType params |

**Rate Limiting**: 150ms delay between paginated requests

**Pagination**: Offset-based with PAGE_SIZE=3000, MAX_PAGES=200

---

## Usage Examples

### Full Historical Backfill
```bash
python -m spread_eagle.ingest.cbb_v2.run_ingest \
    --mode full \
    --start_year 2022 \
    --end_year 2025
```

### Daily Incremental (for Airflow)
```bash
python -m spread_eagle.ingest.cbb_v2.run_ingest \
    --mode incremental
```

### Specific Datasets Only
```bash
python -m spread_eagle.ingest.cbb_v2.run_ingest \
    --mode incremental \
    --datasets games,lines,team_game_stats
```

### Files Only (no DB)
```bash
python -m spread_eagle.ingest.cbb_v2.run_ingest \
    --mode full \
    --no-db
```

### Database Only (no files)
```bash
python -m spread_eagle.ingest.cbb_v2.run_ingest \
    --mode incremental \
    --no-files
```

---

## Dataset Load Order

The orchestrator loads datasets in dependency order:

1. `teams` - Reference data, no dependencies
2. `venues` - Reference data, no dependencies
3. `games` - Core transactional data
4. `team_game_stats` - Depends on games
5. `lines` - Depends on games
6. `team_season_stats` - Aggregated from games
7. `player_season_stats` - Aggregated player data
8. `game_players` - Per-game player details

---

## Error Handling

- Each dataset loads independently
- Errors in one dataset don't stop others
- Results include success/error status per dataset
- Exit code 1 if any dataset fails
- Detailed error messages in output

---

## Airflow Integration

For Airflow, create a simple DAG that calls the orchestrator:

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'cbb_ingest',
    default_args=default_args,
    schedule_interval='0 6 * * *',  # Daily at 6 AM
    catchup=False,
)

ingest_task = BashOperator(
    task_id='run_cbb_ingest',
    bash_command='python -m spread_eagle.ingest.cbb_v2.run_ingest --mode incremental',
    dag=dag,
)
```

---

## Migration from V1

The V2 pipeline creates new files with `_v2` suffix and uses a separate schema (`cbb_raw`).
This allows running V1 and V2 in parallel during migration.

After validation:
1. Remove old V1 files from `data/cbb/raw/`
2. Drop or archive old tables if needed
3. Rename V2 files if desired

---

## Future Enhancements

- [ ] Add data quality checks
- [ ] Add metrics/monitoring hooks
- [ ] Add retry logic for API failures
- [ ] Add parallel dataset loading option
- [ ] Add date-based CDC (pull only games from last N days)
