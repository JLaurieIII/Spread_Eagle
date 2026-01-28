# STYLE GUIDE — Spread Eagle

## 1) Purpose of this file (consistency-driven)
- Enforce consistent patterns across dbt, Python, SQL, and LLM prompts
- Reduce cognitive load when switching contexts
- Make AI-generated code predictable and maintainable
- Prevent “clever” solutions that hurt clarity
- Ensure future contributors follow the same rules

**Rule:** If a pattern is not written here, it is not a standard.

---

## 2) General principles (apply everywhere)

- Prefer clarity over cleverness
- Prefer explicit over implicit
- Prefer boring, readable solutions
- Optimize for debuggability, not brevity
- Write as if future-you is tired and skeptical

If two solutions work, choose the one that is easier to explain.

---

## 3) Naming conventions (global)

### Tables
- Prefix by role:
  - `dim__` → dimensions
  - `fct__` → facts
  - `ui__` → UI-ready summaries
  - `feat__` → model features
  - `pred__` → model outputs
  - `content__` → LLM-generated content
- Use double underscores consistently
- Include sport only when necessary (e.g., staging)

### Columns
- snake_case only
- No ambiguous names (`value`, `metric`, `score`)
- Prefer descriptive names (`rolling_margin_L10`, not `margin10`)
- Boolean columns prefixed with `is_` or `has_`

---

## 4) dbt style rules (non-negotiable)

### Model structure
- One model = one responsibility
- Use CTEs for logical steps
- Avoid deeply nested queries
- No SELECT *

### Descriptions and tests
- Every model must have:
  - a description
  - explicit grain in the description
- Tests required:
  - not_null on primary keys
  - unique where grain requires it
  - accepted_values or ranges where applicable

### Transform rules
- Deterministic math only
- No randomness
- No model-specific logic in dbt
- No business logic in the app

---

## 5) Python style rules

### General
- Type hints where practical
- Small, composable functions
- Separate IO from computation
- No hidden globals

### Data access
- Read only from dbt-built tables
- Write only to defined output tables
- Never silently overwrite data

### Modeling
- Baseline logic must be readable
- ML code must be reproducible
- Always version model outputs
- Log inputs, date ranges, and counts

---

## 6) SQL style rules

- Uppercase SQL keywords
- One column per line in SELECT
- Explicit JOIN conditions
- No implicit joins
- Order CTEs logically (raw → cleaned → derived)

SQL should be readable without execution context.

---

## 7) LLM prompt style

### Tone
- Informative
- Entertaining but responsible
- No guarantees
- No false certainty

### Prompt structure
- Clear role assignment
- Explicit constraints
- Grounded context only (RAG)
- Deterministic formatting where possible

### Output rules
- TL;DR must:
  - explain what’s interesting
  - explain what’s risky
  - avoid telling users what to bet
- LLM output never feeds numeric models

---

## 8) UI-facing data rules

- UI reads from tables only
- UI never computes metrics
- UI never joins more than necessary
- One card = one primary table (max two)

If the UI needs logic, the data model is wrong.

---

## 9) Documentation hygiene

- Update `/ai_context/` when behavior changes
- Do not let docs drift from reality
- Keep files short and authoritative
- Prefer fewer documents with clear purpose

---

## 10) Style invariants (do not break)

- Consistency beats optimization
- Explicit beats clever
- Determinism beats novelty
- Readability beats speed
- Trust beats hype
