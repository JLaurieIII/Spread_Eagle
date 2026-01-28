# AI CONTEXT PACK — START HERE

## 1) Project identity (read this first)

**Project name:** Spread Eagle

**One-liner (precise, no fluff):**
Spread Eagle is a sports analytics platform that ingests raw sportsbook and game data, models outcome distributions, and outputs **calibrated probabilities** (not picks) for moneyline, spread, totals, and teaser-adjusted lines — with variance as a first-class concept.

**True goal (not negotiable):**
Identify *predictable* betting environments by modeling variance and tail behavior — especially for teaser bets — rather than chasing directional edges alone.

---

## 2) The Session Journal (CRITICAL — read immediately after this file)

**File:** `SESSION_JOURNAL.md`

The Session Journal is the living memory of this project. It bridges sessions and prevents context loss.

**Why it matters:**
- This project moves fast across multiple workstreams (data, dbt, ML, UI, API)
- Humans switch gears often and forget context
- AI sessions start fresh and need to understand what just happened
- Decisions made in one session affect the next

**Rules:**
1. **At session start:** Read the CURRENT STATE section of `SESSION_JOURNAL.md` immediately after this file
2. **At session end:** Update the journal before closing — add what was done, feedback received, and what's next
3. **When switching gears:** Add a brief entry noting the pivot and why
4. **Never skip this.** Silent context loss is a project killer.

The journal is not optional documentation — it is **operational infrastructure**.

---

## 3) Core philosophy (how to think)

- This project is **probability-first**, not picks-first.
- Every output must be explainable in terms of **distribution + variance**, not vibes.
- Teasers are **window bets**, therefore **variance dominates direction**.
- Uncertainty is allowed; **overconfidence is a bug**.

If something improves hit rate but worsens calibration, it is considered a regression.

---

## 4) Canonical definitions (do not drift)

- **Directional bet:** A bet on one side of a spread/total/moneyline.
- **Teaser:** A bet where the line is shifted ±N points; success depends on outcome distribution width.
- **Skinny tails:** Low-variance outcome distribution → teaser-friendly.
- **Fat tails:** High-variance outcome distribution → teaser-hostile.
- **High confidence:** A probability range justified by historical calibration, not raw win rate.

These definitions are fixed unless explicitly changed in `05_DECISIONS.md`.

---

## 5) What the system actually does (end-to-end)

1. Ingest raw sportsbook lines + game/team/player data
2. Store raw data unchanged
3. Transform via dbt into clean, well-grained fact + feature tables
4. Compute variance and distribution-aware features
5. Generate **probabilities** for:
   - Moneyline
   - Spread
   - Total
   - Teaser-adjusted spreads/totals
6. Serve results to a consumer-facing app or API

There is no step where "gut feel" is introduced.

---

## 6) Hard rules for AI collaborators

- Do **not** redesign architecture unless `05_DECISIONS.md` says so.
- Do **not** introduce new metrics without:
  - Grain
  - Formula
  - dbt model location
- Always prefer **baseline + backtest** before complex modeling.
- If unsure, propose an assumption **and document it**.

Silent assumptions are considered failures.

**Additional rule:** Always update `SESSION_JOURNAL.md` at session end. This is not optional.

---

## 7) Where to look next (mandatory order)

After reading this file:

1. **Read `SESSION_JOURNAL.md`** (CURRENT STATE section)
   → understand what just happened, what's working, what's broken
2. **Read `04_TASKS.md`**
   → understand what to do next
3. **Reference `05_DECISIONS.md`**
   → avoid re-litigating settled choices
4. **Use other files only as needed**

Before ending session:
- **Update `SESSION_JOURNAL.md`** with what you did and what's next

---

## 8) Current focus (update when it changes)

**Right now, the project is focused on:**
- Adding visualizations and graphs to game cards
- Building variance/teaser analysis features
- Creating a prediction tracking system
- Identifying teaser-friendly game pairs

**What's Working (as of 2026-01-24):**
- Dashboard at localhost:3002 with 142 real games
- API at localhost:8001 serving `/cbb/dashboard` endpoint
- Team records, PPG, pace, recent form, last 5 games all displayed
- Date navigation functional

**Secondary (do after primary):**
- Producing teaser-specific probability outputs
- Building confidence buckets that are *actually calibrated*
- Multi-sport support (CFB, NFL, etc.)

Anything not directly supporting this is lower priority.

---

## 9) Rehydration prompt (copy/paste after restart)

> You are working on the Spread Eagle project.
> Read `AI_memory/00_START_HERE.md` first.
> Then read `AI_memory/SESSION_JOURNAL.md` (especially CURRENT STATE).
> Then read `AI_memory/04_TASKS.md`.
> Propose the next 3 concrete actions.
> Do not redesign architecture or redefine goals unless explicitly stated in `AI_memory/05_DECISIONS.md`.
> **Before ending session:** Update SESSION_JOURNAL.md with what you did and what's next.
