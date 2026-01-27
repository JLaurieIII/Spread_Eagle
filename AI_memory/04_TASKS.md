# TASKS — Spread Eagle

## 1) Purpose of this file (task-driven)
- Define what work is actively in scope
- Prevent random feature drift
- Keep daily progress concrete and measurable
- Provide a clear “what’s next” for humans and AI collaborators
- Separate execution from strategy and architecture

**Rule:** If a task is not listed here, it is not actively being worked on.

---

## 2) How tasks are organized (canonical)

Tasks are grouped into three buckets only:
- **NOW** → must be completed to move the product forward
- **NEXT** → queued once NOW is complete
- **LATER** → explicitly deferred, not forgotten

Each task should:
- Be concrete and testable
- Produce an observable artifact (table, script, output, UI change)
- Move the product closer to a usable daily CBB experience

---

## 3) NOW — Active work (blocking progress)

### Visualization & Analysis (TOP PRIORITY)
- [ ] Add graphs/charts to game detail view (pace, scoring trends)
- [ ] Display variance indicators per game (teaser-friendly flag)
- [ ] Show probability distributions where available
- [ ] Build teaser finder — identify low-variance game pairs

### Prediction Tracking System
- [ ] Design database schema for picks/predictions
- [ ] Create API endpoints for saving/retrieving predictions
- [ ] Build UI for making and viewing predictions
- [ ] Track historical accuracy

### Data Quality & Cleanup
- [ ] Delete UI_V2 folder (locked by process — manual)
- [ ] Review and clean up unused files
- [ ] Add more team colors to API color mapping

### COMPLETED ✅
- [x] Create API endpoint for CBB games: `GET /cbb/dashboard?date=YYYY-MM-DD`
- [x] Build dbt mart model: `fct_cbb__game_dashboard`
- [x] Frontend fetches real data from API (142 games for test date)
- [x] Team records (overall, conf, ATS, O/U) displayed
- [x] PPG, pace, recent form shown
- [x] Last 5 games with spread results
- [x] Date navigation working
- [x] Timezone bug fixed

---

## 4) NEXT — Near-term follow-ups

### Modeling
- Create baseline probability logic (rules-first)
- Build `feat__game_market_features`
- Generate first version of `pred__game_market`
- Add basic calibration checks and confidence buckets

### LLM TL;DR
- Define RAG context payload (which fields are passed)
- Create prompt template for TL;DR generation
- Store outputs in `content__game_tldr`
- Validate tone: fun, informative, no guarantees

### UI Readiness
- Ensure UI-facing tables:
  - `ui__game_context`
  - `ui__betting_snapshot`
  exist and are stable
- Validate that each UI card can be rendered with ≤2 queries

---

## 5) LATER — Explicitly deferred

- Advanced variance modeling (distribution fitting, tail modeling)
- Injury/news integration
- Market movement modeling beyond open/close
- Real-time or intraday updates
- Multi-sport support beyond CBB
- Premium gating and monetization logic
- Cloud-native orchestration (MWAA / ECS / etc.)

These items are intentionally deferred to protect focus.

---

## 6) Task hygiene rules (do not violate)

- No “quick hacks” that bypass dbt
- No new tables without adding them to `03_DATA_MODEL.md`
- No new features without tying them to a UI card
- No architecture changes without updating `02_ARCHITECTURE.md`
- When a task is completed, move it out of NOW

---

## 7) Definition of “MVP complete”

The CBB MVP is considered complete when:
- The pipeline runs daily without manual steps
- All CBB games for the day populate correctly
- Each game renders all core UI cards
- Variance data is present and sane
- TL;DR content is generated automatically
- You personally want to use it before placing a bet

Until then, scope does not expand.
