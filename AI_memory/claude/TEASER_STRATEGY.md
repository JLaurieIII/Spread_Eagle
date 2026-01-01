# Teaser Strategy - Low Volatility Edge

The core betting thesis for Spread Eagle.

---

## What is a Teaser?

A teaser lets you adjust the spread in your favor in exchange for:
1. Lower payout odds
2. Must parlay 2+ selections (all must win)

**Example:**
```
Standard bet:    Alabama -7 at -110
2-team teaser:   Alabama -1 at -110 (moved 6 points)
                 + Ohio State -3 at -110 (moved 6 points)
                 Both must cover to win
```

---

## The Edge: Low Volatility Teams

### The Insight

Most bettors treat all teams equally when teasing. But teams have DIFFERENT variance profiles:

```
HIGH VOLATILITY TEAM (Bad teaser candidate)
├── ATS margins: [-15, +20, -8, +25, -3, +18, -12, ...]
├── Mean: +3.5
├── Std Dev: 15.2
└── Outcome: Unpredictable, teasing doesn't help much

LOW VOLATILITY TEAM (Good teaser candidate)
├── ATS margins: [+5, +3, +7, +4, +6, +2, +5, +4, ...]
├── Mean: +4.5
├── Std Dev: 1.8
└── Outcome: Clustered around +4-5, teasing 6 pts = near-certain cover
```

### The Math

If a team's ATS margin is normally distributed with mean μ and std σ:

```
P(cover at spread S) = P(margin > -S)
                     = Φ((μ + S) / σ)

Where Φ is the standard normal CDF.

Example - Team with mean +4, std 2:
- P(cover at -7) = Φ((4+7)/2) = Φ(5.5) = 99.99%
- P(cover at -3) = Φ((4+3)/2) = Φ(3.5) = 99.98%

Example - Team with mean +4, std 12:
- P(cover at -7) = Φ((4+7)/12) = Φ(0.92) = 82%
- P(cover at -3) = Φ((4+3)/12) = Φ(0.58) = 72%

The low-volatility team is MUCH safer to tease!
```

---

## Why CBB is Better Than CFB

| Factor | CFB | CBB |
|--------|-----|-----|
| Games per season | 12-15 | 30-35 |
| Sample size for variance | Limited | Robust |
| Back-to-backs | Rare | Common (exploitable) |
| Line efficiency | Very sharp | Less efficient |
| Teaser availability | Yes | Yes |
| Variance stability | Changes week to week | More stable patterns |

**Key insight:** CBB gives us 2-3x more data per team per season, making variance estimates more reliable.

---

## Implementation Plan

### Step 1: Build Variance Profile Model

```sql
-- fct_cbb__variance_profile.sql

SELECT
    team_id,
    team_name,

    -- Central tendency
    AVG(ats_margin) as ats_mean_l20,

    -- VOLATILITY MEASURES
    STDDEV(ats_margin) as ats_std_l20,

    -- Distribution shape
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ats_margin) as ats_p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ats_margin) as ats_p75,

    -- Teaser-specific metrics
    COUNT(*) FILTER (WHERE ABS(ats_margin) <= 7) / COUNT(*)::float
        as pct_within_7_pts,

    COUNT(*) FILTER (WHERE ats_margin > 0) / COUNT(*)::float
        as cover_rate,

    -- Tail risk
    COUNT(*) FILTER (WHERE ats_margin < -10) / COUNT(*)::float
        as blowout_loss_rate,

    -- Sample size
    COUNT(*) as games_in_window

FROM int_cbb__game_team_lines
WHERE game_date > CURRENT_DATE - INTERVAL '90 days'
GROUP BY team_id, team_name
HAVING COUNT(*) >= 10  -- Minimum sample
```

### Step 2: Identify Teaser Candidates

```sql
-- fct_cbb__teaser_candidates.sql

WITH upcoming AS (
    SELECT * FROM fct_cbb__upcoming_predictions
),

team_variance AS (
    SELECT * FROM fct_cbb__variance_profile
),

candidates AS (
    SELECT
        u.*,
        tv.ats_std_l20 as team_volatility,
        ov.ats_std_l20 as opp_volatility,

        -- Teaser adjustment
        u.spread_close_for_team + 6 as teased_spread_6pt,
        u.spread_close_for_team + 7 as teased_spread_7pt,

        -- Probability estimates (simplified)
        -- Real model would use XGBoost
        CASE
            WHEN tv.ats_std_l20 < 6 THEN 'HIGH'
            WHEN tv.ats_std_l20 < 8 THEN 'MEDIUM'
            ELSE 'LOW'
        END as teaser_confidence

    FROM upcoming u
    JOIN team_variance tv ON u.team_id = tv.team_id
    JOIN team_variance ov ON u.opponent_id = ov.team_id

    WHERE tv.ats_std_l20 < 8  -- Low volatility filter
      AND tv.games_in_window >= 15  -- Sufficient sample
      AND tv.pct_within_7_pts > 0.5  -- Historical teaser success
)

SELECT * FROM candidates
ORDER BY team_volatility ASC  -- Lowest volatility first
```

### Step 3: Train Teaser-Specific Model

```python
# spread_eagle/ml/train_teaser_model.py

Features:
- team_volatility (ats_std_l20)
- opp_volatility
- current_spread
- teased_spread
- team_cover_rate_l20
- rest_differential
- home_away

Label:
- would_cover_teased (computed: ats_margin > -teased_spread)

Model:
- XGBoost classifier
- Or: Direct probability calculation using variance estimate
```

### Step 4: Backtest

```python
# spread_eagle/ml/backtest_teasers.py

For each historical game:
1. Check if team qualified as low-volatility at that time
2. Simulate 6pt and 7pt teasers
3. Track win rate
4. Calculate ROI at standard teaser odds (-110 for 2-team)

Output:
- Win rate by volatility bucket
- ROI by teaser type
- Optimal volatility threshold
```

---

## Teaser Parlay Math

### Standard 2-Team Teaser Odds

| Teaser Points | Odds | Implied Probability |
|---------------|------|---------------------|
| 6 points | -110 | 52.4% per leg needed |
| 6.5 points | -120 | 54.5% per leg needed |
| 7 points | -130 | 56.5% per leg needed |

### Break-Even Analysis

For a 2-team teaser at -110:
- Need both legs to win
- Required probability per leg: √0.524 = 72.4%
- If each leg has 75% true probability: EV = +6.25%

**Our target:** Find legs with 75%+ probability of covering teased line.

---

## Key Metrics to Track

### Per-Team Metrics
| Metric | What It Tells Us |
|--------|------------------|
| `ats_std_l20` | Core volatility measure |
| `pct_within_7_pts` | Teaser success rate |
| `ats_mean_l20` | Systematic bias |
| `blowout_loss_rate` | Tail risk |

### Per-Game Metrics
| Metric | What It Tells Us |
|--------|------------------|
| `p_cover_standard` | Raw cover probability |
| `p_cover_teased` | Teased cover probability |
| `edge` | p_cover_teased - break_even |
| `combined_volatility` | Team vol + Opp vol |

---

## Risk Management

### What Could Go Wrong

1. **Regime change** - Team's volatility pattern changes mid-season
2. **Key injuries** - Variance profile no longer valid
3. **Small sample** - Early season estimates unreliable
4. **Correlation** - Both legs of teaser lose together
5. **Line movement** - Spread moves against us

### Mitigation

1. **Recency weighting** - Weight recent games more heavily
2. **Injury adjustments** - Monitor key player statuses
3. **Sample minimums** - Require 15+ games in window
4. **Diversification** - Don't parlay correlated games
5. **Early betting** - Capture value before line moves

---

## Implementation Priority

### Week 1: Data Foundation
- [ ] Verify CBB data quality
- [ ] Build CBB staging models
- [ ] Build CBB intermediate models
- [ ] Build fct_cbb__variance_profile

### Week 2: Model Development
- [ ] Build fct_cbb__teaser_candidates
- [ ] Create teaser label in historical data
- [ ] Train teaser probability model
- [ ] Initial backtest

### Week 3: Validation
- [ ] Out-of-sample testing
- [ ] Paper trading (track without betting)
- [ ] Refine volatility thresholds
- [ ] Build teaser UI components

### Week 4: Deployment
- [ ] Airflow automation
- [ ] Daily teaser candidate alerts
- [ ] Track actual results
- [ ] Iterate on model
