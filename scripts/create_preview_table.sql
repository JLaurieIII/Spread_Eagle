-- ============================================================
-- Game Previews Table (AI-generated content, not a dbt transform)
-- ============================================================
-- Run: psql -U postgres -d spread_eagle -f scripts/create_preview_table.sql
-- ============================================================

CREATE TABLE IF NOT EXISTS cbb.game_previews (
    id                SERIAL PRIMARY KEY,
    game_id           INTEGER NOT NULL,
    game_date         DATE NOT NULL,
    headline          TEXT NOT NULL,
    tldr              TEXT NOT NULL,
    body              TEXT NOT NULL,
    spread_pick       TEXT,
    spread_rationale  TEXT,
    ou_pick           TEXT,
    ou_rationale      TEXT,
    confidence        TEXT,              -- HIGH / MEDIUM / LOW
    key_factors       JSONB DEFAULT '[]',
    articles_used     JSONB DEFAULT '[]',
    raw_llm_response  JSONB,
    model_used        TEXT DEFAULT 'gpt-4o',
    prompt_version    TEXT DEFAULT 'v1',
    tokens_used       INTEGER,
    generation_time_ms INTEGER,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    expires_at        TIMESTAMPTZ,
    CONSTRAINT uq_game_preview_per_day UNIQUE (game_id, game_date)
);

CREATE INDEX IF NOT EXISTS idx_game_previews_game_date ON cbb.game_previews (game_date);
