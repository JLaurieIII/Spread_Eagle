# SESSION JOURNAL — Spread Eagle

> **Purpose:** This is the living memory of the project. Every AI session should read this first (after `00_START_HERE.md`) and write to it last. Humans should update it when making decisions outside of AI sessions.

---

## CURRENT STATE (always update this section)

**Last updated:** 2026-01-24
**Last session focus:** Full dashboard build - API + Frontend connected to real data
**Current blocker:** None - dashboard is working
**Next priority:** Add more intel per game (graphs, variance analysis, teaser finder)

### What's Working
- **DASHBOARD FULLY OPERATIONAL** ✅
- **UI running on localhost:3002** with real data from API
- **API running on localhost:8001** serving CBB dashboard endpoint
- Fresh data ingest completed (420K+ rows loaded to local + AWS RDS)
- New dbt mart model: `fct_cbb__game_dashboard` with comprehensive game data
- New API endpoint: `GET /cbb/dashboard?date=YYYY-MM-DD` returning 142 games
- Dashboard shows:
  - Game list with mini tiles (date navigation works)
  - Team records (overall, conference, ATS, O/U)
  - PPG, OPP PPG, Pace stats
  - Recent form (W/L dots)
  - Last 5 games with spread results
  - Betting lines (spread + total)
- JavaScript timezone issue fixed (dates now display correctly)
- Logo copied to `ui/public/logo.jpeg`

### What's Not Working / Missing
- No graphs or visualizations per game yet
- No variance/teaser analysis calculations shown in UI
- No predictions or pick tracking
- UI_V2 folder still exists (locked, needs manual deletion)
- CFB data pipeline not active

### Active Decisions Pending
- How to structure prediction tracking for past games
- What graphs/visualizations to add per game card

### Next Up
1. Add more intel per game (graphs, charts)
2. Build variance/teaser analysis view
3. Add prediction tracking system
4. Clean up UI_V2 folder (manual delete)

### Architecture Overview
```
[API Data Sources] → [Ingest Scripts] → [Parquet] → [PostgreSQL]
                                                          ↓
                                                    [dbt models]
                                                          ↓
                                              [marts_cbb.fct_cbb__game_dashboard]
                                                          ↓
                                              [FastAPI: /cbb/dashboard]
                                                          ↓
                                              [Next.js UI: localhost:3002]
```

### Infrastructure Status
| Component | Local | AWS |
|-----------|-------|-----|
| PostgreSQL | ✅ localhost:5432/spread_eagle | ✅ RDS (data loaded) |
| API | ✅ localhost:8001 | Not deployed |
| UI | ✅ localhost:3002 | Not deployed |
| dbt | ✅ target: local | target: aws (available) |

---

## HOW TO USE THIS JOURNAL

### For AI Collaborators

**At session start:**
1. Read `00_START_HERE.md` (project identity, philosophy)
2. Read this journal's CURRENT STATE section (what just happened)
3. Read `04_TASKS.md` (what's in scope)
4. Begin work

**At session end or when switching gears:**
1. Update CURRENT STATE section above
2. Add a dated entry below with:
   - What was done
   - What feedback was given
   - What's next
   - Any decisions made

**Rule:** Never leave a session without updating this journal. Future you (or future AI) will thank you.

### For Humans

Update this journal when:
- You make a decision outside an AI session
- You receive feedback from users/testers
- Priorities change
- You're about to start a new session and want to set direction

---

## SESSION ENTRIES (newest first)

---

### 2026-01-24 — Full Dashboard Build: API + Frontend Connected

**Session type:** Feature build (major)
**Duration:** ~2 hours
**Focus:** Build complete CBB dashboard with real data from API

#### What Was Done

1. **Fresh data ingest**
   - Ran `python -m spread_eagle.ingest.cbb.run_full_load` (pulled fresh parquet)
   - Loaded to local PostgreSQL: 420,855 rows
   - Loaded to AWS RDS: Same dataset synced

2. **Built new dbt mart model: `fct_cbb__game_dashboard`**
   - Location: `dbt_transform/models/marts/cbb/fct_cbb__game_dashboard.sql`
   - Combines: games, betting lines, team records, ATS/O/U records, rolling stats, volatility
   - Uses "latest" CTEs to handle scheduled games (gets most recent team data)
   - Returns 31K+ rows covering all CBB games with full stats

3. **Built new API endpoint: `GET /cbb/dashboard`**
   - Location: `spread_eagle/api/routers/cbb.py`
   - Queries the dbt mart model
   - Returns comprehensive game data for UI cards:
     - Game info (date, time, venue, location)
     - Both teams with: record, conf record, ATS, O/U, PPG, pace
     - Recent form (last 5 W/L)
     - Last 5 games with scores and spread results
     - Betting lines (spread, total)
   - Team colors mapped for 50+ major programs

4. **Rewrote frontend to fetch from API**
   - Location: `ui/app/page.tsx`
   - Removed all mock data
   - Added `fetchDashboardGames()` to call API
   - Date navigation (prev/next buttons)
   - Loading and error states
   - Scrollable game list for 140+ game days
   - Fixed JavaScript timezone issue (was showing wrong day)

5. **Fixed timezone bug**
   - Problem: `new Date("2026-01-24")` parses as UTC → displays as previous day
   - Solution: Created `createLocalDate(year, month, day)` helper
   - `formatDateForAPI()` now uses local timezone methods

6. **Preserved assets**
   - Copied `docs/logo.jpeg` to `ui/public/logo.jpeg`
   - UI_V2 folder marked for deletion (locked by process)

#### Technical Details

**API Response Shape:**
```json
{
  "date": "2026-01-24",
  "count": 142,
  "games": [{
    "id": 211083,
    "gameDate": "Sat, Jan 24",
    "gameTime": "11am",
    "venue": "...",
    "spread": "TEAM -3.5",
    "total": "167.5",
    "homeTeam": {
      "name": "...", "shortName": "...", "primaryColor": "#...",
      "record": "12-5", "confRecord": "3-2", "atsRecord": "8-8-0",
      "ouRecord": "10-6-0", "ppg": 78.5, "oppPpg": 72.3, "pace": 68.5,
      "recentForm": ["W","W","L","W","L"],
      "last5Games": [...]
    },
    "awayTeam": { ... }
  }]
}
```

**Key Files Changed:**
- `dbt_transform/models/marts/cbb/fct_cbb__game_dashboard.sql` — NEW
- `spread_eagle/api/routers/cbb.py` — Added dashboard models + endpoint
- `ui/app/page.tsx` — Rewrote to fetch from API
- `ui/.env.local` — API URL config

#### Feedback Received

> "I only see 10 games showing on 3002 and they don't appear to be todays games"
→ Fixed: Was defaulting to actual current date (2025), changed to 2026-01-24 for test data

> "The dates are off... you have all the games for today 1/24 as 1/23"
→ Fixed: JavaScript timezone issue with Date parsing

> "I want there to be more intel per game, I want graphs... variance outcomes... teaser finder"
→ Noted: This is the next phase of development

#### What's Next

1. **Add visualizations** — Graphs for pace, scoring trends, etc.
2. **Variance analysis** — Show teaser-friendly indicators per game
3. **Prediction tracking** — System to make and track picks
4. **Clean up** — Delete UI_V2 folder manually

#### Open Questions

- What specific graphs would be most valuable per game?
- How to structure prediction tracking (database tables needed?)
- Should past dates show historical predictions/results?

---

### 2026-01-16 (evening) — Game Card Enhancement: ATS & O/U Records

**Session type:** Feature build
**Duration:** ~45 min
**Focus:** Add team betting records (ATS and O/U) to game cards in UI_V2

#### What Was Done

1. **Enhanced API endpoint with betting records**
   - Updated `GET /cbb/games` to calculate ATS (against the spread) records per team
   - Added O/U (over/under) records per team from completed games
   - SQL aggregates betting outcomes from `cbb.games` + `cbb.betting_lines` (Bovada)
   - Records displayed as "W-L-P" format (e.g., "9-6-0", "5-7-1")

2. **Updated Pydantic models**
   - Added `ats_record` and `ou_record` optional fields to `TeamInfo` model
   - Both fields are nullable (teams without betting history show as null)

3. **Enhanced frontend GameCard component**
   - Added betting records section below team names
   - Displays ATS and O/U in a clean 3-column grid
   - Shows both teams' records side by side
   - Only renders if at least one team has betting data

#### Technical Details

**ATS Calculation Logic:**
- Home team covers if: `home_margin + spread > 0`
- Away team covers if: `-home_margin - spread > 0`
- Push if margin equals spread exactly

**O/U Calculation Logic:**
- Over if: `total_points > over_under`
- Under if: `total_points < over_under`
- Push if: `total_points = over_under`

#### Files Changed

- `spread_eagle/api/routers/cbb.py` — Added betting record CTEs and fields
- `UI_V2/app/cbb/page.tsx` — Added betting records display to GameCard

#### What's Next

1. Create game detail page (`/cbb/[id]`) — wire up "View Analysis" button
2. Add more data to game cards (rankings, injury info)
3. Build out the analysis view with variance data

---

### 2026-01-16 — Local Development Environment & AWS Cleanup

**Session type:** Infrastructure / DevOps
**Duration:** ~1 hour
**Focus:** Eliminate AWS costs, set up fully local development stack

#### What Was Done

1. **Deleted expensive Aurora Serverless cluster from AWS**
   - Found 4 RDS resources: Aurora cluster + 2 Serverless v2 instances + 1 db.t4g.micro
   - Aurora was NOT created by Terraform (manual console creation)
   - Deleted via AWS CLI: reader instance → writer instance → cluster
   - Kept only the Terraform-managed db.t4g.micro (~$12/mo, can be stopped)

2. **Configured local development environment**
   - Updated `.env` to point to `localhost:5432/spread_eagle`
   - Updated `~/.dbt/profiles.yml` with `local` and `aws` targets (default: local)
   - Created `ENVIRONMENTS.md` — quick reference for switching environments

3. **Created separate PostgreSQL loader scripts**
   - `load_to_postgres_local.py` — no SSL, for local development
   - `load_to_postgres_rds.py` — SSL required, with safety warning for AWS
   - Original `load_to_postgres.py` kept for reference

4. **Ran full CBB ingest + load + dbt pipeline locally**
   - Ingest scripts pulled fresh data from API to parquet files
   - Loaded 419,169 rows to local PostgreSQL in 42 seconds
   - dbt ran 15 CBB models successfully (staging → intermediate → marts)

5. **Verified marts tables**
   - `fct_cbb__teaser_matchups`: 2,413 rows
   - `fct_cbb__ml_features_ou`: 2,420 rows
   - `int_cbb__team_rolling_stats`: 55,244 rows
   - `int_cbb__team_spread_volatility`: 4,826 rows

#### Feedback Received

> "I'm concerned with how these were created in the first place" (re: Aurora cluster)
> "I am paying money I don't have and it's not worth it while I build"

#### Technical Decisions Made

| Decision | Choice | Why |
|----------|--------|-----|
| Aurora cluster | Delete entirely | Not from Terraform, expensive, unnecessary for dev |
| Environment switching | `.env` + dbt profiles | Simple, no code changes needed |
| Separate loader scripts | local vs RDS files | SSL requirements differ, clearer intent |
| dbt Python version | Use `.venv312` | Python 3.14 has dbt compatibility issues |

#### What's Next

1. **Create game detail page (`/cbb/[id]`)** — wire up "View Analysis" button
2. **Start using local stack for daily development** — no more AWS costs
3. **Consider stopping the db.t4g.micro** — save ~$12/mo until ready for prod

#### Files Created/Changed

- `.env` — Now points to local PostgreSQL
- `~/.dbt/profiles.yml` — Added local/aws targets
- `ENVIRONMENTS.md` — Environment switching guide (new)
- `spread_eagle/ingest/cbb/load_to_postgres_local.py` — New local loader
- `spread_eagle/ingest/cbb/load_to_postgres_rds.py` — New RDS loader

#### Key Commands for Future Reference

```bash
# Run ingest scripts
python -m spread_eagle.ingest.cbb.run_full_load

# Load to local PostgreSQL
python -m spread_eagle.ingest.cbb.load_to_postgres_local

# Run dbt (must use Python 3.12 venv)
cd dbt_transform && .venv312/Scripts/dbt run --select tag:cbb

# Switch to AWS (when needed)
copy .env.aws .env
# Edit ~/.dbt/profiles.yml: target: aws
```

---

### 2026-01-15 (Part 2) — Frontend-Backend Integration

**Session type:** Integration
**Duration:** ~45 min
**Focus:** Connect UI_V2 to backend API for real CBB game data

#### What Was Done

1. **Created Session Journal infrastructure**
   - `AI_memory/SESSION_JOURNAL.md` — living memory with CURRENT STATE section
   - Updated `00_START_HERE.md` with Section 2 emphasizing journal importance
   - Updated `04_TASKS.md` with Frontend ↔ Backend as TOP PRIORITY

2. **Added API endpoint: `GET /cbb/games?date=YYYY-MM-DD`**
   - File: `spread_eagle/api/routers/cbb.py`
   - Queries `cbb.games` joined with `cbb.betting_lines` and `cbb.team_season_stats`
   - Returns: teams, records, spreads, totals, venues, scores
   - Smart team short name generation with abbreviation lookup

3. **Fixed import error in `spread_eagle/api/main.py`**
   - Moved `Base` import from database.py to models.py

4. **Updated UI_V2 CBB page to fetch from API**
   - Removed mock data
   - Added `useEffect` to fetch games when date changes
   - Added loading spinner and error handling
   - "View Analysis" button now links to `/cbb/[gameId]`

#### Feedback Received

> "This is beautiful" (on UI design)
> "Let's connect frontend and backend today"

#### Technical Decisions Made

| Decision | Choice | Why |
|----------|--------|-----|
| API response shape | Match frontend mock data shape | Minimal frontend changes needed |
| Team short names | Abbreviation lookup + fallback | Common CBB abbreviations matter |
| Date timezone | Eastern Time for game dates | CBB is primarily US-based |
| Betting lines provider | Bovada | Most common provider in dataset |

#### What's Next

1. **Create game detail page (`/cbb/[id]`)** — wire up "View Analysis" button
2. **Add rankings to API** — pull from poll data or calculate from stats
3. **Test with actual game dates** — verify data flows correctly

#### Files Changed

- `AI_memory/SESSION_JOURNAL.md` — Created
- `AI_memory/00_START_HERE.md` — Added Section 2 (journal emphasis)
- `AI_memory/04_TASKS.md` — Added Frontend ↔ Backend priority
- `spread_eagle/api/routers/cbb.py` — Added `/games` endpoint
- `spread_eagle/api/main.py` — Fixed Base import
- `UI_V2/app/cbb/page.tsx` — Integrated with API

#### Open Questions

- What date range has good CBB data in the database?
- Should rankings come from AP poll data or be calculated?

---

### 2026-01-15 — UI_V2 Foundation

**Session type:** Feature build
**Duration:** ~1 hour
**Focus:** Frontend overhaul — new home page and CBB games experience

#### What Was Done

1. **Created UI_V2 folder** — Cloned from original `ui` folder as authorized workspace

2. **Built new home page (`/`)**
   - Logo prominently displayed (280x280)
   - "SPREAD EAGLE" title with navy blue gradient + red accent
   - Tagline: "Probabilities, Not Picks"
   - Mission statement emphasizing variance and predictable environments
   - Three value prop cards:
     - Distribution-First
     - Teaser-Optimized
     - Calibrated Confidence
   - Sports grid: CBB active, CFB/NFL/NBA/MLB/NHL showing "Coming 2026"
   - Patriotic theme: navy star field (top-left), subtle red stripes (right)
   - Footer with responsible betting disclaimer

3. **Built CBB games page (`/cbb`)**
   - Sticky header with logo and home navigation
   - Date navigation bar with:
     - Arrow buttons for prev/next day
     - Quick jump buttons: Yesterday / Today / Tomorrow
     - Current date display
   - Game cards showing:
     - Conference badge
     - Team matchups with rankings and records
     - Spread and O/U lines
     - Venue and game time
     - "Featured" badge for marquee games
     - "View Analysis" CTA button
   - Past games show final scores
   - Context banners for past/future dates
   - Empty state for no-game days

4. **Updated layout metadata** — Title and description now reflect Spread Eagle branding

#### Feedback Received

> "This is beautiful"

User approved the design direction. Ready to proceed with connecting frontend to backend.

#### Technical Decisions Made

| Decision | Choice | Why |
|----------|--------|-----|
| Folder structure | `/app/cbb/page.tsx` | Next.js 16 app router, clean URL structure |
| Date handling | String-based (`YYYY-MM-DD`) | Simple, timezone-safe, easy to compare |
| Mock data | Inline in component | Quick iteration; will move to API |
| Theme colors | Navy `#0A1628`, Red `#B22234` | Matches logo, patriotic feel |

#### What's Next

1. **Connect frontend to backend** — Priority for today
   - Even if just teams and game times
   - Create API route in UI_V2 or call existing spread_eagle API
   - Replace mock data with real data

2. **Game detail page** — Wire up "View Analysis" button
   - Route: `/cbb/[gameId]`
   - Show the existing game analysis UI

3. **API contract** — Define what the frontend needs:
   - `/api/cbb/games?date=YYYY-MM-DD`
   - Response shape to match current mock data

#### Files Changed

- `UI_V2/app/page.tsx` — New home page
- `UI_V2/app/cbb/page.tsx` — New CBB games page (created)
- `UI_V2/app/layout.tsx` — Updated metadata
- `UI_V2/public/logo.jpeg` — Copied from docs/

#### Open Questions

- Should the backend API live in `spread_eagle/api/` or in `UI_V2/app/api/`?
- What's the current state of CBB data in the database?
- Is there an existing endpoint for games by date?

---

### Template for Future Entries

```markdown
### YYYY-MM-DD — [Brief Title]

**Session type:** [Feature build | Bug fix | Research | Planning | Refactor]
**Duration:** [estimate]
**Focus:** [one sentence]

#### What Was Done
- Bullet points of concrete deliverables

#### Feedback Received
> Quote any user feedback

#### Technical Decisions Made
| Decision | Choice | Why |

#### What's Next
1. Numbered priorities

#### Files Changed
- List of files

#### Open Questions
- Anything unresolved
```

---

## CHANGELOG SUMMARY (for quick scanning)

| Date | Focus | Key Outcome |
|------|-------|-------------|
| 2026-01-24 | Full Dashboard Build | New dbt mart model, dashboard API endpoint, frontend fetches real data, 142 games displayed |
| 2026-01-16 | Local Dev Environment | Deleted Aurora cluster, full local stack working, 419K rows loaded, dbt passing |
| 2026-01-15 (PM) | Frontend-Backend Integration | API endpoint for games by date, UI fetches real data |
| 2026-01-15 (AM) | UI_V2 Foundation | Home page + CBB games view built, patriotic theme applied |

---

## PATTERNS & LESSONS LEARNED

> Add patterns here when you discover something that should be repeated or avoided.

### Do This
- Always update CURRENT STATE at session end
- Quote user feedback verbatim — context matters
- List files changed — makes code review easier
- Use local PostgreSQL for development (no AWS costs)
- Run dbt with `.venv312` (Python 3.12) — Python 3.14 has compatibility issues

### Avoid This
- Don't leave sessions without journaling
- Don't assume previous session context is retained
- Don't skip the "What's Next" section — it's the handoff
- Don't create AWS resources manually — use Terraform so they're tracked
- Don't use Aurora Serverless for dev — overkill and expensive

---

*This journal is the bridge between sessions. Treat it with respect.*
