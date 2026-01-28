# PRODUCT — Spread Eagle

## 1) The problem (personal, practical, honest)

Most people who bet on sports don’t lack information — they lack **organization, context, and restraint**.

Bettors today:
- Open 10 tabs (scores, odds, stats, Twitter)
- Bet out of boredom or impulse
- Miss key context (variance, pace, recent form)
- Don’t know when *not* to bet

Spread Eagle exists to be a **one-stop betting intelligence app**:
- everything you need to understand today’s games
- nothing pretending to guarantee outcomes

---

## 2) What Spread Eagle actually is (plain English)

Spread Eagle is a **daily sports betting companion**.

For each sport:
- You see all games for the day
- You click a game
- You get a small set of **clean, focused cards** that:
  - set the stage
  - summarize the matchup
  - highlight risk vs opportunity
  - help you decide whether to bet or pass

It is not a pick service.  
It is not a sportsbook.  
It is not a prediction machine.

It is decision support.

---

## 3) Initial scope (explicit)

### Phase 1 (MVP)
- **Sport:** College Basketball (CBB)
- **Mode:** Fully automated, daily refresh
- **Audience:** You + early serious bettors
- **Cost-aware:** Runs cheaply, scales later

### Expansion (planned, not rushed)
- MLB (April)
- NFL, NBA, NHL, CFB
- Shared product shape across sports

Multi-sport support is a goal, but **CBB must feel polished before expansion**.

---

## 4) Core game experience (non-negotiable)

Each game page should feel lightweight but complete.

### Card 1 — Game Context
Purpose: *Set the stage*

Includes:
- Teams, location, time
- Records (overall, ATS, O/U)
- Last 3 games
- Key averages (pace, scoring, margin)
- Anything that helps a bettor “feel” the game

No analysis yet. Just grounding.

---

### Card 2 — Betting Snapshot
Purpose: *What is the market saying?*

Includes:
- Current lines (spread / total / moneyline)
- Opening vs current (if available)
- Simple implied probabilities
- Where the public *might* be leaning (if known)

This card is descriptive, not judgmental.

---

### Card 3 — TL;DR (LLM-generated)
Purpose: *Make it fun and human*

- Generated via LLM + RAG
- Entertaining, readable, slightly irreverent
- “Barstool-adjacent,” but not reckless
- Explicitly **no guarantees**

Tone:
> “Here’s what’s interesting. Here’s what’s risky. Here’s why this game could get weird.”

This card is about engagement and comprehension.

---

### Card 4 — Variance & Risk Profile
Purpose: *Where Spread Eagle differentiates*

Includes:
- Variance / volatility indicators
- Skinny vs fat tail classification
- Historical stability vs chaos signals
- Teaser friendliness (when applicable)

This may start simple and grow deeper over time.

Initially **free**, eventually a **premium pillar**.

---

### Optional Card 5 — Deeper Insights (later)
- Advanced metrics
- Historical comps
- Model-backed probabilities
- Confidence buckets

Not required for MVP.

---

## 5) Behavior change we are encouraging

**Before Spread Eagle:**
- Betting because “I want action”
- Betting without full context
- Ignoring risk and volatility
- Overbetting marginal edges

**After Spread Eagle:**
- Betting fewer games
- Passing with confidence
- Understanding *why* a game is risky
- Using variance as a filter, not an afterthought

If users say *“this talked me out of a bet”*, the product is working.

---

## 6) Role of variance (clarified)

Variance modeling is:
- A **core differentiator**
- A **research pillar**
- A **premium expansion path**

But it is **not a prerequisite** to enjoy or use the app.

The product must be valuable:
- even before advanced variance modeling is fully mature
- even to users who don’t want to think in distributions (yet)

Variance should **enhance**, not block, adoption.

---

## 7) What this product refuses to become

Spread Eagle will NOT:
- Sell locks
- Rank “best bets”
- Guarantee ROI
- Hide uncertainty
- Optimize for reckless volume

If engagement ever depends on deception, the product has failed.

---

## 8) Success criteria (early)

### MVP success looks like:
- Fully automated daily CBB run
- Clean UI with 4–5 cards per game
- Data refreshes reliably
- TL;DR feels alive, not generic
- You personally want to use it daily

If you wouldn’t bet with it yourself, it’s not done.

---

## 9) Product north star

Spread Eagle should feel like:

> “Everything I need to understand today’s games —  
> without being told what to bet.”

That sentence should remain true even as the system grows.
