# PROMPTS — Spread Eagle

## 1) Purpose of this file (behavior-driven)
- Define canonical prompts that shape AI behavior
- Make Claude / ChatGPT predictable and aligned
- Reduce prompt thrash and “prompt engineering by vibes”
- Ensure outputs respect product, data, and architecture constraints
- Speed up development by reusing known-good prompts

**Rule:** If a prompt pattern works, it lives here. If it’s not here, it’s not standard.

---

## 2) How prompts are used (canonical)

Prompts in this file are:
- Copy/paste ready
- Opinionated and constrained
- Designed to be reused across sessions
- Written to survive AI restarts and context loss

Prompts should:
- Declare role clearly
- Declare constraints explicitly
- Reference `/ai_context/` files when relevant
- Produce deterministic structure where possible

---

## 3) Rehydration prompt (mandatory on restart)

### Project re-entry
