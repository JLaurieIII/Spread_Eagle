# DECISIONS — Spread Eagle

## 1) Purpose of this file (decision-driven)
- Record irreversible or expensive-to-change decisions
- Prevent re-litigating settled questions
- Give future-you and AI collaborators clear guardrails
- Explain *why* the system is the way it is, not just *what* it is
- Reduce cognitive load during development

**Rule:** If a decision is not written here, it is not locked.

---

## 2) How decisions are captured (canonical)

Each decision should:
- Be explicit and opinionated
- State the chosen option
- State what was rejected
- State the reason in plain language
- Describe the consequences

Decisions are stable and only change deliberately.

---

## 3) Product-level decisions

### Betting intelligence, not picks
- **Decision:** Spread Eagle will provide probabilities, context, and risk signals — not picks.
- **Rejected:** “Best bets,” locks, rankings.
- **Why:** Picks encourage overconfidence and irresponsible behavior.
- **Consequence:** UI and marketing must emphasize decision support and passing as valid outcomes.

---

### Fun tone without deception
- **Decision:** Use a fun, barstool-adjacent tone via LLM TL;DRs.
- **Rejected:** Purely academic or purely hype-driven presentation.
- **Why:** Engagement matters, but trust matters more.
- **Consequence:** TL;DRs must include uncertainty and never guarantee outcomes.

---

### Variance as a differentiator, not a gatekeeper
- **Decision:** Variance and volatility modeling is core but not required to use the app.
- **Rejected:** Blocking basic usage behind advanced variance understanding.
- **Why:** Adoption comes before depth.
- **Consequence:** Variance starts simple and grows over time; advanced views may become premium.

---

## 4) Data and modeling decisions

### dbt as the single transform layer
- **Decision:** All deterministic transformations live in dbt.
- **Rejected:** Computing metrics ad-hoc in Python or the UI.
- **Why:** Reproducibility, testability, and clarity.
- **Consequence:** Slower iteration upfront, far less pain later.

---

### Explicit grain everywhere
- **Decision:** Every table must declare its grain explicitly.
- **Rejected:** Implicit or assumed grains.
- **Why:** Silent grain bugs are the most expensive bugs.
- **Consequence:** Some tables feel redundant, but correctness is preserved.

---

### Baseline-first modeling
- **Decision:** Start with rule-based and historical baselines before ML.
- **Rejected:** Jumping straight to complex models.
- **Why:** Faster validation and better intuition.
- **Consequence:** Baselines remain as benchmarks even after ML is added.

---

### Models consume features, not raw data
- **Decision:** Python models only read from `feat__*` tables.
- **Rejected:** Models joining raw or fact tables directly.
- **Why:** Prevent logic duplication and training/serving skew.
- **Consequence:** Feature tables may grow large but remain authoritative.

---

## 5) Architecture and execution decisions

### Laptop-first orchestration
- **Decision:** Run daily pipelines on a personal laptop initially.
- **Rejected:** Cloud orchestration from day one.
- **Why:** Cost control and faster iteration.
- **Consequence:** Code must be portable to cloud schedulers later.

---

### Postgres as the initial warehouse
- **Decision:** Use AWS RDS Postgres as the primary warehouse.
- **Rejected:** Immediate move to Redshift/Snowflake/BigQuery.
- **Why:** Simplicity, cost, and sufficient scale for MVP.
- **Consequence:** Schema design must remain analytics-friendly.

---

### Batch-first, not real-time
- **Decision:** Daily batch refresh is sufficient for MVP.
- **Rejected:** Streaming or intraday real-time updates.
- **Why:** Betting decisions are typically daily; complexity not justified yet.
- **Consequence:** Users will not see minute-by-minute line movement initially.

---

## 6) LLM-specific decisions

### LLMs generate content, not truth
- **Decision:** LLM output is stored as content only.
- **Rejected:** Feeding LLM text into numeric models.
- **Why:** Prevent hallucination from contaminating data.
- **Consequence:** Clear separation between `content__*` and numeric tables.

---

### RAG-grounded summaries only
- **Decision:** All TL;DRs must be grounded in retrieved data.
- **Rejected:** Free-form generative summaries.
- **Why:** Maintain factual accuracy.
- **Consequence:** Slightly more engineering, far more trust.

---

## 7) Scope and expansion decisions

### CBB-first focus
- **Decision:** College Basketball is the first fully polished sport.
- **Rejected:** Multi-sport MVP.
- **Why:** Depth beats breadth.
- **Consequence:** Expansion only happens after CBB feels complete.

---

### Shared data model across sports
- **Decision:** All sports reuse the same table families.
- **Rejected:** Sport-specific schemas.
- **Why:** Easier expansion and maintenance.
- **Consequence:** Some sport-specific edge cases require careful modeling.

---

## 8) What requires a new decision entry

A new entry is required if:
- Architecture changes materially
- A new execution environment is introduced
- A modeling philosophy changes
- Monetization affects product shape
- A previously rejected idea is reconsidered

If it’s expensive to undo, it belongs here.

---

## 9) Decision invariants (do not violate)

- Decisions are written before being forgotten
- Decisions are not changed casually
- Decisions explain trade-offs, not perfection
- Silence does not imply agreement
- This file outranks memory and intuition
