# Spread Eagle — Meet “Baldy”
> Page build spec + copy deck (hand this to an AI agent)

## Goal
Create a single, high-converting character page introducing **Baldy** (the Spread Eagle persona) and explaining how the daily AI previews work.
Tone: funny, gritty Philly vibe, patriotic, sports-obsessed. Not mean-spirited. Not hateful. Not “guaranteed lock” gambling advice.

---

## Assets
### Primary image
- File: `A_character_portrait_photo_features_"Spread_Eagle_.png`
- Use as: hero image (desktop: right side; mobile: top)
- Alt text: `Baldy the Spread Eagle — a patriotic bald eagle gambler with a Philly attitude`

---

## Page requirements
### Tech
- Build as a responsive page (works on mobile first).
- Include a sticky CTA button: **“See Today’s Picks”** linking to `/cbb` (or your picks landing page).
- Add a secondary CTA: **“How it works”** anchor link to the “One call per game” section.

### SEO
- Title: `Meet Baldy: The Spread Eagle Who Picks College Basketball Games`
- Meta description (155–160 chars):
  `Meet Baldy—Spread Eagle’s patriotic Philly bald eagle who drops one AI-generated college basketball preview per game per day. Funny. Sharp. Cached.`

### Safety / Responsible gaming
Include a short disclaimer footer on the page and in the “How it works” section:
- “For entertainment only. No guarantees. Please bet responsibly.”

---

## Page structure + copy (ready to paste)

## HERO
### H1
Meet **Baldy** — Spread Eagle’s Most Patriotic Degenerate

### Subhead
A sharp-tongued Philly bald eagle who loves America, college hoops, and the occasional questionable wager — and somehow still brings receipts.

### CTA buttons
- Primary: **See Today’s Picks**
- Secondary: **How it works**

### Hero bullets (short)
- **One AI preview per game per day** (cached, fast, consistent)
- **Grounded in data + news** (injuries, line movement, context)
- **Punchy picks**: spread / total / moneyline lean — with reasons

---

## SECTION: WHO IS BALDY?
### Header
Who the hell is Baldy?

### Body
Baldy is the unofficial commissioner of Spread Eagle — a bald eagle with a Philly attitude and a suspiciously high confidence in mid-major unders.

He’s not a villain. He’s not a saint. He’s the friend who shows up wearing an American-flag jacket, calls the refs “bozos,” and somehow explains tempo, turnovers, and free-throw rate better than half the internet.

### Quick facts (cards)
- **Species:** Bald Eagle (obviously)
- **Hometown:** South Philly (spiritually, at least)
- **Fuel:** caffeine, chaos, and the smell of a close line
- **Special skill:** turning stats into trash talk — fast

---

## SECTION: BALDY’S BIO (WEBPAGE VERSION)
### Header
Baldy’s Bio

Baldy “Spread Eagle” McGraw (no relation, don’t ask) is a loud, lovable, slightly unhinged bald eagle who lives for two things: **America** and **a number that makes sense**.

He watches college basketball like it owes him money. He’s allergic to soft analysis. If a team’s rebounding stinks or their point guard turns it over like it’s a hobby, Baldy’s gonna tell you — loudly — and then he’s gonna tell you what he’s doing about it.

He’s funny. He’s blunt. He’s occasionally dramatic. But he’s built on one rule:
**No pick without a reason.**

---

## SECTION: WHAT YOU GET (THE DAILY PREVIEW)
### Header
What Baldy delivers every day

Each game gets a single daily preview with:
- **Headline** (punchy, memeable, Baldy-approved)
- **TL;DR prediction** (who wins and why in 2–4 sentences)
- **Spread pick** (with rationale + confidence)
- **Total pick** (Over/Under lean + matchup logic)
- **Moneyline lean** (when it matters)
- **Key factors** (tempo, shooting profile, TOs, rebounding, foul rate, travel/rest)
- **Risk notes** (how this pick could blow up)

Add a line under this list:
> Baldy doesn’t do “locks.” He does **angles**.

---

## SECTION: HOW IT WORKS (THE TECH, SIMPLIFIED)
### Header
One call per game. No spam. No rerolls.

### Body (plain English)
Spread Eagle generates **one** AI preview per game **per day** — then stores it in a database so your page loads instantly and the take stays consistent.

Under the hood:
1. We pull structured matchup data (team performance, recent form, style)
2. We check fresh news (injuries, suspensions, notable updates, line movement)
3. We run **one** model call to write Baldy’s preview
4. We cache the result in Postgres so it’s fast, reproducible, and cheap

### Micro-disclaimer (required)
> For entertainment only. No guarantees. Bet responsibly.

---

## SECTION: BALDY QUOTES (FUN)
### Header
Things Baldy says a lot

Use as rotating quote component:
- “That line is begging you to get emotional. Don’t.”
- “If you don’t rebound, you don’t deserve happiness.”
- “I don’t hate the pick. I hate that I like it.”
- “Tempo tells the truth. The rest is noise.”
- “Vegas sets the center. We hunt the shape.”

---

## SECTION: CTA / NEWSLETTER (OPTIONAL)
### Header
Want Baldy in your inbox?

Short copy:
Get the daily slate, the best angles, and the games Baldy refuses to touch.

Fields:
- Email input
- Button: **Send the slate**

---

## FOOTER DISCLAIMER (REQUIRED)
**Disclaimer:** Spread Eagle content is for entertainment and informational purposes only and is not betting or financial advice. Outcomes are uncertain. Please bet responsibly.

---

## Design notes (for the agent)
- Overall vibe: modern sports media + slightly gritty bar-room personality
- Use the hero image prominently
- Add subtle “patriotic grit” styling (navy/red accents), but keep it clean
- Keep paragraphs short and scannable
- Use icon bullets and small “confidence meter” visuals (optional)

---

## Deliverables (what the agent should output)
1. A finished webpage (HTML/React/Next — whatever this project uses)
2. The hero image placed and optimized (responsive sizing)
3. Metadata: title + meta description
4. All copy above implemented
5. Responsive layout verified on mobile and desktop
