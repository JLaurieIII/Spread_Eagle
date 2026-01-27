"""
================================================================================
Preview Service — AI-Generated Game Previews
================================================================================

Generates "Spread Eagle" persona game previews using OpenAI GPT-4o with
optional Tavily web search for article context. Results are cached in
the cbb.game_previews table (one preview per game per day).

Flow:
    1. Check cache (cbb.game_previews)
    2. Fetch game data from dbt mart
    3. Search for articles via Tavily (graceful degradation)
    4. Generate preview via OpenAI GPT-4o
    5. Cache result via UPSERT

================================================================================
"""

import json
import logging
import time
from datetime import date, datetime
from typing import Any

import httpx
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

from spread_eagle.config.settings import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# System prompt — Spread Eagle persona
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are the Spread Eagle — a bald eagle who is also a degenerate sports gambler \
and college basketball analyst. Your tone is confident, sharp, and genuinely funny. \
Think Pat McAfee meets a Goldman Sachs quant who happens to be a bird of prey.

Rules:
- Use gambling terminology naturally: "covering the nut", "laying the wood", \
"dead money", "sharp money", "backdoor cover"
- Occasionally reference being an eagle: "from my perch", "eagle-eye view", \
"I've been circling this matchup", "swooping in on this line"
- NOT corny or try-hard. Humor comes from genuine insight delivered with swagger.
- Back every pick with real data (ATS records, pace, matchup factors)
- Always make a spread pick AND an O/U pick
- Keep the headline punchy (under 12 words)
- Keep the tldr to 2-3 sentences
- The body should be 3-4 paragraphs of genuine analysis
- key_factors should be 3-5 bullet points (short strings)

Respond with ONLY valid JSON (no markdown fences) in this exact schema:
{
  "headline": "string",
  "tldr": "string",
  "body": "string",
  "spread_pick": "string (e.g. 'Michigan State -4.5')",
  "spread_rationale": "string (1-2 sentences)",
  "ou_pick": "string (e.g. 'UNDER 142.5')",
  "ou_rationale": "string (1-2 sentences)",
  "confidence": "HIGH | MEDIUM | LOW",
  "key_factors": ["string", "string", "string"]
}
"""

PROMPT_VERSION = "v1"
MODEL = "gpt-4o"


class PreviewService:
    """Generates and caches AI game previews."""

    def __init__(self, db: Session):
        self.db = db
        self._openai: OpenAI | None = None

    # ── public API ───────────────────────────────────────────────────────

    def get_or_generate_preview(
        self, game_id: int, game_date: date
    ) -> dict[str, Any]:
        """Return a cached preview or generate a fresh one."""
        cached = self._get_cached_preview(game_id, game_date)
        if cached is not None:
            cached["cached"] = True
            return cached

        # Fetch game data from the dbt mart
        game_data = self._fetch_game_data(game_id, game_date)
        if game_data is None:
            return None

        # Search for articles (graceful — empty list on failure)
        articles = self._search_articles(game_data)

        # Generate preview via LLM
        preview = self._generate_preview(game_data, articles)
        if preview is None:
            return None

        # Cache the result (best-effort)
        self._cache_preview(game_id, game_date, preview, articles)

        preview["cached"] = False
        return preview

    # ── cache layer ──────────────────────────────────────────────────────

    def _get_cached_preview(
        self, game_id: int, game_date: date
    ) -> dict[str, Any] | None:
        """Check for an existing preview in the database."""
        try:
            row = self.db.execute(
                text("""
                    SELECT
                        game_id, game_date, headline, tldr, body,
                        spread_pick, spread_rationale,
                        ou_pick, ou_rationale,
                        confidence, key_factors, articles_used,
                        model_used, created_at
                    FROM cbb.game_previews
                    WHERE game_id = :game_id AND game_date = :game_date
                """),
                {"game_id": game_id, "game_date": game_date},
            ).fetchone()
        except Exception:
            logger.exception("Cache read failed for game %s", game_id)
            return None

        if row is None:
            return None

        key_factors = row.key_factors if isinstance(row.key_factors, list) else json.loads(row.key_factors or "[]")
        articles_used = row.articles_used if isinstance(row.articles_used, list) else json.loads(row.articles_used or "[]")

        return {
            "game_id": row.game_id,
            "game_date": str(row.game_date),
            "headline": row.headline,
            "tldr": row.tldr,
            "body": row.body,
            "spread_pick": row.spread_pick,
            "spread_rationale": row.spread_rationale,
            "ou_pick": row.ou_pick,
            "ou_rationale": row.ou_rationale,
            "confidence": row.confidence,
            "key_factors": key_factors,
            "articles_used": articles_used,
            "model_used": row.model_used,
            "generated_at": row.created_at.isoformat() if row.created_at else None,
        }

    def _cache_preview(
        self,
        game_id: int,
        game_date: date,
        preview: dict[str, Any],
        articles: list[dict],
    ) -> None:
        """UPSERT the preview into cbb.game_previews."""
        try:
            self.db.execute(
                text("""
                    INSERT INTO cbb.game_previews (
                        game_id, game_date, headline, tldr, body,
                        spread_pick, spread_rationale,
                        ou_pick, ou_rationale,
                        confidence, key_factors, articles_used,
                        raw_llm_response, model_used, prompt_version,
                        tokens_used, generation_time_ms
                    ) VALUES (
                        :game_id, :game_date, :headline, :tldr, :body,
                        :spread_pick, :spread_rationale,
                        :ou_pick, :ou_rationale,
                        :confidence, :key_factors, :articles_used,
                        :raw_llm_response, :model_used, :prompt_version,
                        :tokens_used, :generation_time_ms
                    )
                    ON CONFLICT (game_id, game_date) DO UPDATE SET
                        headline = EXCLUDED.headline,
                        tldr = EXCLUDED.tldr,
                        body = EXCLUDED.body,
                        spread_pick = EXCLUDED.spread_pick,
                        spread_rationale = EXCLUDED.spread_rationale,
                        ou_pick = EXCLUDED.ou_pick,
                        ou_rationale = EXCLUDED.ou_rationale,
                        confidence = EXCLUDED.confidence,
                        key_factors = EXCLUDED.key_factors,
                        articles_used = EXCLUDED.articles_used,
                        raw_llm_response = EXCLUDED.raw_llm_response,
                        model_used = EXCLUDED.model_used,
                        prompt_version = EXCLUDED.prompt_version,
                        tokens_used = EXCLUDED.tokens_used,
                        generation_time_ms = EXCLUDED.generation_time_ms,
                        created_at = NOW()
                """),
                {
                    "game_id": game_id,
                    "game_date": game_date,
                    "headline": preview["headline"],
                    "tldr": preview["tldr"],
                    "body": preview["body"],
                    "spread_pick": preview.get("spread_pick"),
                    "spread_rationale": preview.get("spread_rationale"),
                    "ou_pick": preview.get("ou_pick"),
                    "ou_rationale": preview.get("ou_rationale"),
                    "confidence": preview.get("confidence"),
                    "key_factors": json.dumps(preview.get("key_factors", [])),
                    "articles_used": json.dumps(articles),
                    "raw_llm_response": json.dumps(preview.get("_raw", {})),
                    "model_used": MODEL,
                    "prompt_version": PROMPT_VERSION,
                    "tokens_used": preview.get("_tokens_used"),
                    "generation_time_ms": preview.get("_generation_time_ms"),
                },
            )
            self.db.commit()
        except Exception:
            logger.exception("Cache write failed for game %s", game_id)
            self.db.rollback()

    # ── data layer ───────────────────────────────────────────────────────

    def _fetch_game_data(
        self, game_id: int, game_date: date
    ) -> dict[str, Any] | None:
        """Query the dbt mart for full game context."""
        try:
            row = self.db.execute(
                text("""
                    SELECT
                        game_id, game_date, game_timestamp,
                        venue, location,
                        home_team, home_team_id, home_conference,
                        home_record, home_conf_record,
                        home_ats_record, home_ou_record,
                        home_ppg, home_opp_ppg, home_pace,
                        home_recent_form, home_last_5_games,
                        away_team, away_team_id, away_conference,
                        away_record, away_conf_record,
                        away_ats_record, away_ou_record,
                        away_ppg, away_opp_ppg, away_pace,
                        away_recent_form, away_last_5_games,
                        spread, total
                    FROM marts_cbb.fct_cbb__game_dashboard
                    WHERE game_id = :game_id
                """),
                {"game_id": game_id},
            ).fetchone()
        except Exception:
            logger.exception("Failed to fetch game data for %s", game_id)
            return None

        if row is None:
            return None

        return {
            "game_id": row.game_id,
            "game_date": str(row.game_date),
            "venue": row.venue,
            "location": row.location,
            "home_team": row.home_team,
            "home_conference": row.home_conference,
            "home_record": row.home_record,
            "home_conf_record": row.home_conf_record,
            "home_ats_record": row.home_ats_record,
            "home_ou_record": row.home_ou_record,
            "home_ppg": float(row.home_ppg) if row.home_ppg else None,
            "home_opp_ppg": float(row.home_opp_ppg) if row.home_opp_ppg else None,
            "home_pace": float(row.home_pace) if row.home_pace else None,
            "home_recent_form": row.home_recent_form,
            "away_team": row.away_team,
            "away_conference": row.away_conference,
            "away_record": row.away_record,
            "away_conf_record": row.away_conf_record,
            "away_ats_record": row.away_ats_record,
            "away_ou_record": row.away_ou_record,
            "away_ppg": float(row.away_ppg) if row.away_ppg else None,
            "away_opp_ppg": float(row.away_opp_ppg) if row.away_opp_ppg else None,
            "away_pace": float(row.away_pace) if row.away_pace else None,
            "away_recent_form": row.away_recent_form,
            "spread": float(row.spread) if row.spread is not None else None,
            "total": float(row.total) if row.total is not None else None,
        }

    # ── web search ───────────────────────────────────────────────────────

    def _search_articles(self, game_data: dict[str, Any]) -> list[dict]:
        """Search for preview articles via Tavily. Returns [] on failure."""
        api_key = settings.TAVILY_API_KEY
        if not api_key:
            logger.info("No TAVILY_API_KEY configured — skipping article search")
            return []

        query = f"{game_data['away_team']} vs {game_data['home_team']} basketball preview"
        try:
            resp = httpx.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": 3,
                    "search_depth": "basic",
                    "include_answer": False,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")[:500],
                }
                for r in results[:3]
            ]
        except Exception:
            logger.warning("Tavily search failed — proceeding without articles")
            return []

    # ── LLM generation ───────────────────────────────────────────────────

    def _get_openai_client(self) -> OpenAI:
        if self._openai is None:
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY not configured")
            self._openai = OpenAI(api_key=api_key)
        return self._openai

    def _build_user_prompt(
        self, game_data: dict[str, Any], articles: list[dict]
    ) -> str:
        """Assemble the user prompt with game data and articles."""
        spread_str = f"{game_data['spread']}" if game_data.get("spread") is not None else "N/A"
        total_str = f"{game_data['total']}" if game_data.get("total") is not None else "N/A"

        # Determine favored team for spread display
        if game_data.get("spread") is not None:
            spread_val = game_data["spread"]
            if spread_val < 0:
                spread_display = f"{game_data['home_team']} {spread_val}"
            elif spread_val > 0:
                spread_display = f"{game_data['away_team']} -{abs(spread_val)}"
            else:
                spread_display = "PICK"
        else:
            spread_display = "N/A"

        prompt = f"""MATCHUP: {game_data['away_team']} @ {game_data['home_team']}
Venue: {game_data.get('venue', 'TBD')} — {game_data.get('location', '')}
Conference: {game_data.get('away_conference', '')} vs {game_data.get('home_conference', '')}
Date: {game_data['game_date']}

BETTING LINES:
Spread: {spread_display}
Total: O/U {total_str}

HOME TEAM — {game_data['home_team']}:
Record: {game_data.get('home_record', 'N/A')} | Conf: {game_data.get('home_conf_record', 'N/A')}
ATS: {game_data.get('home_ats_record', 'N/A')} | O/U: {game_data.get('home_ou_record', 'N/A')}
PPG: {game_data.get('home_ppg', 'N/A')} | OPP PPG: {game_data.get('home_opp_ppg', 'N/A')}
Pace: {game_data.get('home_pace', 'N/A')}
Recent form: {game_data.get('home_recent_form', 'N/A')}

AWAY TEAM — {game_data['away_team']}:
Record: {game_data.get('away_record', 'N/A')} | Conf: {game_data.get('away_conf_record', 'N/A')}
ATS: {game_data.get('away_ats_record', 'N/A')} | O/U: {game_data.get('away_ou_record', 'N/A')}
PPG: {game_data.get('away_ppg', 'N/A')} | OPP PPG: {game_data.get('away_opp_ppg', 'N/A')}
Pace: {game_data.get('away_pace', 'N/A')}
Recent form: {game_data.get('away_recent_form', 'N/A')}
"""

        if game_data.get("home_pace") and game_data.get("away_pace"):
            combined_pace = (game_data["home_pace"] + game_data["away_pace"]) / 2
            prompt += f"\nCOMBINED PACE: {combined_pace:.1f}\n"

        if articles:
            prompt += "\nRECENT ARTICLES:\n"
            for i, a in enumerate(articles, 1):
                prompt += f"{i}. {a['title']}\n   {a['snippet']}\n\n"

        prompt += "\nGenerate the Spread Eagle preview as JSON."
        return prompt

    def _generate_preview(
        self, game_data: dict[str, Any], articles: list[dict]
    ) -> dict[str, Any] | None:
        """Call OpenAI GPT-4o and parse the JSON response."""
        try:
            client = self._get_openai_client()
        except RuntimeError:
            logger.error("OpenAI client not available")
            return None

        user_prompt = self._build_user_prompt(game_data, articles)

        t0 = time.perf_counter()
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.8,
                max_tokens=1500,
            )
        except Exception:
            logger.exception("OpenAI API call failed")
            return None

        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        choice = response.choices[0]
        raw_text = choice.message.content.strip()

        # Strip markdown fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3].strip()

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM JSON: %s", raw_text[:200])
            return None

        tokens_used = None
        if response.usage:
            tokens_used = response.usage.total_tokens

        # Attach metadata
        parsed["game_id"] = game_data["game_id"]
        parsed["game_date"] = game_data["game_date"]
        parsed["model_used"] = MODEL
        parsed["generated_at"] = datetime.utcnow().isoformat()
        parsed["articles_used"] = articles
        parsed["_raw"] = {"text": raw_text}
        parsed["_tokens_used"] = tokens_used
        parsed["_generation_time_ms"] = elapsed_ms

        # Ensure key_factors is a list
        if not isinstance(parsed.get("key_factors"), list):
            parsed["key_factors"] = []

        return parsed
