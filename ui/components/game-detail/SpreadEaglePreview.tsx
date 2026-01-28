"use client";

import React, { useEffect, useState } from "react";

// API Base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

// ============================================================================
// Types
// ============================================================================

interface ArticleSource {
  title: string;
  url: string;
  snippet: string;
}

interface PreviewData {
  game_id: number;
  game_date: string;
  headline: string;
  tldr: string;
  body: string;
  spread_pick: string | null;
  spread_rationale: string | null;
  ou_pick: string | null;
  ou_rationale: string | null;
  confidence: string | null;
  key_factors: string[];
  articles_used: ArticleSource[];
  model_used: string;
  generated_at: string | null;
  cached: boolean;
}

interface SpreadEaglePreviewProps {
  gameId: number;
  currentDate: string; // YYYY-MM-DD
}

// ============================================================================
// Helper
// ============================================================================

function cn(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

// ============================================================================
// Component
// ============================================================================

export default function SpreadEaglePreview({
  gameId,
  currentDate,
}: SpreadEaglePreviewProps) {
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function fetchPreview() {
      setIsLoading(true);
      setError(null);
      setPreview(null);
      setIsExpanded(false);

      try {
        const resp = await fetch(
          `${API_BASE_URL}/cbb/preview/${gameId}?date=${currentDate}`
        );
        if (!resp.ok) {
          throw new Error(`${resp.status}`);
        }
        const data: PreviewData = await resp.json();
        if (!cancelled) {
          setPreview(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    fetchPreview();
    return () => {
      cancelled = true;
    };
  }, [gameId, currentDate]);

  // ── Loading state ───────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="rounded-xl border border-amber-200/60 bg-amber-50/50 p-5">
        <div className="flex items-center gap-3">
          <span className="text-2xl animate-bounce">🦅</span>
          <span className="text-sm font-medium text-amber-800 italic">
            The Eagle is circling this matchup...
          </span>
        </div>
      </div>
    );
  }

  // ── Error / unavailable — hide silently ─────────────────────────────
  if (error || !preview) {
    return null;
  }

  // ── Confidence badge color ──────────────────────────────────────────
  const confidenceColor: Record<string, string> = {
    HIGH: "bg-emerald-100 text-emerald-800 border-emerald-300",
    MEDIUM: "bg-amber-100 text-amber-800 border-amber-300",
    LOW: "bg-slate-100 text-slate-600 border-slate-300",
  };
  const confClass =
    confidenceColor[preview.confidence?.toUpperCase() ?? ""] ??
    confidenceColor.LOW;

  return (
    <div className="rounded-xl border border-slate-200 bg-white/90 overflow-hidden">
      {/* Header bar */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100 bg-slate-50/60">
        <div className="flex items-center gap-2">
          <span className="text-lg">🦅</span>
          <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
            Spread Eagle Preview
          </span>
        </div>
        <div className="flex items-center gap-2">
          {preview.confidence && (
            <span
              className={cn(
                "text-xs font-bold uppercase px-2.5 py-0.5 rounded-full border",
                confClass
              )}
            >
              {preview.confidence} Confidence
            </span>
          )}
        </div>
      </div>

      <div className="p-5 space-y-4">
        {/* Headline */}
        <h3 className="text-lg font-black text-slate-800 leading-snug">
          &ldquo;{preview.headline}&rdquo;
        </h3>

        {/* TL;DR */}
        <div className="border-l-4 border-slate-800 pl-4 py-1">
          <p className="text-sm text-slate-700 leading-relaxed">
            <span className="font-bold text-slate-800">TL;DR: </span>
            {preview.tldr}
          </p>
        </div>

        {/* Picks row */}
        <div className="grid grid-cols-2 gap-3">
          {/* Spread pick */}
          {preview.spread_pick && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="text-xs font-bold uppercase tracking-wide text-slate-500 mb-1">
                Spread Pick
              </div>
              <div className="text-base font-black text-slate-800">
                {preview.spread_pick}
              </div>
              {preview.spread_rationale && (
                <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                  {preview.spread_rationale}
                </p>
              )}
            </div>
          )}

          {/* O/U pick */}
          {preview.ou_pick && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="text-xs font-bold uppercase tracking-wide text-slate-500 mb-1">
                O/U Pick
              </div>
              <div className="text-base font-black text-slate-800">
                {preview.ou_pick}
              </div>
              {preview.ou_rationale && (
                <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                  {preview.ou_rationale}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Key factors */}
        {preview.key_factors && preview.key_factors.length > 0 && (
          <div>
            <div className="text-xs font-bold uppercase tracking-wide text-slate-500 mb-2">
              Key Factors
            </div>
            <ul className="space-y-1">
              {preview.key_factors.map((factor, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-slate-700"
                >
                  <span className="text-slate-400 mt-0.5">▸</span>
                  <span>{factor}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Expandable body */}
        {preview.body && (
          <div>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-1.5 text-sm font-semibold text-slate-600 hover:text-slate-800 transition-colors"
            >
              <span
                className={cn(
                  "transition-transform duration-200 inline-block",
                  isExpanded ? "rotate-90" : ""
                )}
              >
                ▶
              </span>
              {isExpanded ? "Hide full analysis" : "Read full analysis"}
            </button>

            {isExpanded && (
              <div className="mt-3 space-y-3">
                <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                  {preview.body}
                </div>

                {/* Article sources */}
                {preview.articles_used && preview.articles_used.length > 0 && (
                  <div className="pt-3 border-t border-slate-100">
                    <div className="text-xs font-bold uppercase tracking-wide text-slate-400 mb-1.5">
                      Sources
                    </div>
                    <ul className="space-y-1">
                      {preview.articles_used.map((article, i) => (
                        <li key={i}>
                          <a
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:underline"
                          >
                            {article.title || article.url}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-5 py-2.5 border-t border-slate-100 bg-slate-50/40">
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <span>🦅</span>
          <span>Generated by {preview.model_used}</span>
        </div>
        <span
          className={cn(
            "text-xs px-2 py-0.5 rounded-full",
            preview.cached
              ? "bg-emerald-50 text-emerald-600 border border-emerald-200"
              : "bg-blue-50 text-blue-600 border border-blue-200"
          )}
        >
          {preview.cached ? "Cached" : "Fresh"}
        </span>
      </div>
    </div>
  );
}
