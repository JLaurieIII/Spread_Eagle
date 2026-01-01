# AI Memory System

This folder maintains context between AI coding sessions.

## Purpose

When starting a new conversation with Claude (or any AI), context is lost. These documents help the AI quickly understand:
- What this project is
- Where we left off
- What's working and what's not
- User preferences and patterns

## Folder Structure

```
AI_memory/
├── README.md           # This file
└── claude/             # Claude-specific context
    ├── QUICK_START.md      # Read first - essential orientation
    ├── PROJECT_OVERVIEW.md # Big picture architecture
    ├── CURRENT_STATE.md    # Where we are NOW (update frequently)
    └── SESSION_JOURNAL.md  # Running log of sessions
```

## How to Use

### Starting a New Session

Tell Claude:
> "Read the files in AI_memory/claude/ to understand this project, then let's continue."

Or more specifically:
> "Start by reading AI_memory/claude/QUICK_START.md"

### During Development

Update `CURRENT_STATE.md` when:
- Major features are completed
- Bugs are discovered
- Architecture decisions are made
- Something breaks

Add to `SESSION_JOURNAL.md`:
- At the end of each session
- Brief summary of what was done
- Any issues encountered
- Where you left off

### Best Practices

1. **Keep CURRENT_STATE.md fresh** - This is what the AI reads to know "where are we"
2. **Journal entries don't need to be long** - Bullet points are fine
3. **Include code snippets** when they help explain state
4. **Note user preferences** - How the user likes to work

## For Other AI Models

Create additional subfolders as needed:
```
AI_memory/
├── claude/
├── gpt/
├── gemini/
└── cursor/
```

Each can have model-specific formatting if needed.
