# DATA MODEL — Spread Eagle

## 1) High-level goals (data-model–driven)
- Define a single, authoritative data contract for the entire system
- Prevent grain ambiguity across dbt, modeling, UI, and LLMs
- Make UI cards trivially queryable (1–2 tables max)
- Support multi-sport expansion without schema redesign
- Keep deterministic math in dbt and probabilistic logic in modeling

---

## 2) Canonical grains (non-negotiable)

- **Sport grain**  
  One of {CBB, CFB, NBA, NFL, MLB, NHL}

- **Game grain**  
  1 row per `game_id`

- **Team–game grain**  
  1 row per `(game_id, team_id)`

- **Market snapshot grain**  
  1 row per `(game_id, market_type, provider, snapshot_time)`

- **Feature grain**  
  Explicitly declared per table; usually extends market snapshot grain

**Rule:** If a table’s grain cannot be stated in one sentence, the table does not exist.

---

## 3) Core entity tables (shared across sports)

### `dim__team`
- **Grain:** 1 row per team per sport  
- **Purpose:** team identity and metadata  
- **Used by:** all downstream tables

---

### `fct__game`
- **Grain:** 1 row per game  
- **Purpose:** canonical game record  
- **Used by:** UI context, joins, modeling labels

Includes:
- sport
- game_id
- game_date
- home_team_id
- away_team_id
- venue
- final_score_home
- final_score_away
- game_status

---

### `fct__team_game`
- **Grain:** 1 row per team per game  
- **Purpose:** team-specific performance and rolling context  
- **Used by:** Game Context card, feature generation

Includes:
- team_id
- game_id
- home_away_flag
- team_score
- opponent_score
- margin
- ATS result
- O/U result
- rolling L3 / L5 / L10 metrics

---

## 4) Betting market tables (descriptive layer)

### `fct__market_snapshot`
- **Grain:** 1 row per `(game_id, market_type, provider, snapshot_time)`  
- **Purpose:** capture how the market prices the game over time  
- **Used by:** Betting Snapshot card, feature tables

Includes:
- market_type (spread | total | moneyline)
- line_value
- odds
- implied_probability
- open_vs_current_delta
- snapshot_time

**Rule:** This table contains no opinions, scores, or predictions.

---

## 5) UI-aligned summary tables (card-ready)

### `ui__game_context`
- **Grain:** 1 row per game  
- **Purpose:** power Card 1 (Game Context)

Derived from:
- `fct__game`
- `fct__team_game`

Includes:
- team records
- ATS / O-U records
- recent form (L3/L5)
- key averages (pace, scoring, margin)

---

### `ui__betting_snapshot`
- **Grain:** 1 row per game per market_type  
- **Purpose:** power Card 2 (Betting Snapshot)

Derived from:
- `fct__market_snapshot`

---

## 6) Variance & risk modeling tables (core differentiator)

### `feat__game_variance_profile`
- **Grain:** 1 row per game per market_type  
- **Purpose:** quantify volatility and predictability  
- **Used by:** Variance/Risk card, modeling

Includes:
- stddev of margin (rolling)
- MAE vs closing line
- pct within ±6 / ±10 / ±12
- tail classification (skinny / medium / fat)
- normalized volatility score

---

## 7) Model feature tables (model-ready)

### `feat__game_market_features`
- **Grain:** 1 row per `(game_id, market_type, snapshot_time)`  
- **Purpose:** single input table for modeling

Includes:
- market context
- team form features
- variance features
- pace / tempo
- foul rates (where applicable)
- labels for training (cover, over, etc.)

**Rule:** If a model uses it, it must live here.

---

## 8) Prediction output tables (serving layer)

### `pred__game_market`
- **Grain:** 1 row per `(game_id, market_type, snapshot_time, model_version)`  
- **Purpose:** final numeric truth served to the app

Includes:
- p_home_win
- p_home_cover
- p_over
- teaser_p_6
- teaser_p_10
- teaser_p_12
- confidence_bucket
- model_version
- scored_at

---

## 9) LLM content tables (explicitly non-numeric)

### `content__game_tldr`
- **Grain:** 1 row per game per generation run  
- **Purpose:** store LLM-generated summaries for display

Includes:
- game_id
- generated_text
- context_version
- generated_at

**Rule:** LLM output is content, not data truth.

---

## 10) UI card → table mapping (critical)

- **Card 1 — Game Context**  
  → `ui__game_context`

- **Card 2 — Betting Snapshot**  
  → `ui__betting_snapshot`

- **Card 3 — TL;DR**  
  → `content__game_tldr`

- **Card 4 — Variance & Risk**  
  → `feat__game_variance_profile` (+ `pred__game_market`)

- **Card 5 — Advanced Insights (later)**  
  → `pred__game_market` + `feat__game_market_features`

**Rule:** If a card needs more than two tables, reconsider the model.

---

## 11) Expansion rules (future sports)
- New sports reuse the same table families
- Sport-specific logic lives in:
  - sport-specific staging
  - sport-specific feature calculations
- UI contracts do not change when sports are added

---

## 12) Data model invariants (never break)
- Grain is explicit everywhere
- UI does not compute
- dbt is the single transform truth layer
- Models are versioned and reproducible
- LLM content is never treated as numeric truth
