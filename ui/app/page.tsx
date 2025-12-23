"use client";

import React, { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import {
  Activity,
  ArrowRight,
  ClipboardList,
  CloudRain,
  Flag,
  Gauge,
  MapPin,
  Shield,
  Sparkles,
  Stars,
  ThermometerSun,
  TrendingUp,
  Users,
  Wind,
} from "lucide-react";

/**
 * Spread Eagle — MVP single-game analysis page
 * - Simple game list → click → one-page dashboard
 * - Designed to work "backwards" from a single JSON payload
 *
 * Replace `mockGames` with real API response later.
 */

// -----------------------------
// Types for the payload you want
// -----------------------------

type Percent = number; // 0..100

type Bucket = {
  label: string; // e.g., "Troy wins 1–5"
  pct: Percent; // e.g., 45.45
  tone?: "home" | "away" | "neutral";
};

type Tempo = {
  paceLabel: "SLOW" | "AVERAGE" | "FAST";
  tempoScore: number; // 0..100
  playsPerGameHome: number;
  playsPerGameAway: number;
  secondsPerPlayHome: number;
  secondsPerPlayAway: number;
};

type Weather = {
  summary: string;
  tempF: number;
  windMph: number;
  precipChancePct: number;
  impactScore: number; // 0..100
};

type Availability = {
  summary: string;
  impactScore: number; // 0..100
  notable: { team: "home" | "away"; player: string; status: string; note: string }[];
};

type Market = {
  spread: string; // e.g., "Troy -3.5"
  total: string; // e.g., "O/U 44.5"
  updatedAtLocal: string;
  lineMoveNote?: string;
};

type Model = {
  bestBet: {
    spreadLean: "HOME" | "AWAY" | "PASS";
    totalLean: "OVER" | "UNDER" | "PASS";
    confidence: "LOW" | "MED" | "HIGH";
    volatility: "LOW" | "MED" | "HIGH";
  };
  marginBuckets: Bucket[]; // sums to 100
  totalDeltaBuckets: Bucket[]; // sums to 100 (distance from market total)
  predicted: {
    spread: number; // model spread, positive means home favored
    total: number;
    score: { home: number; away: number };
  };
};

type GameAnalysisPayload = {
  id: string;
  league: "CFB" | "NFL" | "CBB";
  startTimeLocal: string;
  venue: { stadium: string; city: string; region: string };
  home: { name: string; short: string; record?: string };
  away: { name: string; short: string; record?: string };
  tags?: string[];

  market: Market;
  tempo: Tempo;
  weather: Weather;
  availability: Availability;
  coaching: { summary: string; impactScore: number };

  tldr: {
    headline: string;
    paragraph: string;
    bullets: string[];
  };

  model: Model;

  // room for your engineered features later
  features?: Record<string, number | string | boolean>;
};

// -----------------------------
// Mock data (replace later)
// -----------------------------

const mockGames: GameAnalysisPayload[] = [
  {
    id: "cfb-2025-bowl-troy-jsu",
    league: "CFB",
    startTimeLocal: "Tonight • 7:30 PM",
    venue: { stadium: "Liberty Bowl Memorial Stadium", city: "Memphis", region: "TN" },
    home: { name: "Troy Trojans", short: "TROY", record: "8–4" },
    away: { name: "Jacksonville State Gamecocks", short: "JSU", record: "9–3" },
    tags: ["Bowl", "Ground vs Air", "Opt-outs"],

    market: {
      spread: "Troy -3.5",
      total: "O/U 44.5",
      updatedAtLocal: "Updated 6:05 PM",
      lineMoveNote: "Total ticked down 1.0 since open; spread steady.",
    },
    tempo: {
      paceLabel: "SLOW",
      tempoScore: 34,
      playsPerGameHome: 62.1,
      playsPerGameAway: 59.4,
      secondsPerPlayHome: 28.8,
      secondsPerPlayAway: 30.5,
    },
    weather: {
      summary: "Cool, light wind — minimal weather tax",
      tempF: 54,
      windMph: 7,
      precipChancePct: 15,
      impactScore: 18,
    },
    availability: {
      summary: "Troy missing key run-game pieces; JSU mostly intact",
      impactScore: 71,
      notable: [
        {
          team: "home",
          player: "Tae Meadows (RB)",
          status: "Opt-out",
          note: "High-leverage rusher; impacts early-down efficiency",
        },
        {
          team: "home",
          player: "Goose Crowder (QB)",
          status: "Questionable",
          note: "Ankle — mobility/drive sustainability risk",
        },
        {
          team: "away",
          player: "Cam Cook (RB)",
          status: "Active",
          note: "Workhorse; drives clock control and identity",
        },
      ],
    },
    coaching: {
      summary: "No major staff changes; JSU leans run-heavy regardless of script",
      impactScore: 22,
    },
    tldr: {
      headline: "Low-tempo game where availability swings the edge",
      paragraph:
        "This sets up as a clock-control matchup. Troy’s skill-player availability dents their ability to dictate early downs, while JSU’s run identity travels well and shortens the game. The market is pricing Troy as the cleaner roster — your edge comes from weighting who’s actually available and how that changes pace + efficiency.",
      bullets: [
        "JSU rushing attack profiles as ‘pace governor’ (short game)",
        "Troy absences increase three-and-out risk and reduce explosive run rate",
        "Weather is a non-factor; this is mostly a personnel/tempo bet",
      ],
    },
    model: {
      bestBet: {
        spreadLean: "AWAY",
        totalLean: "UNDER",
        confidence: "MED",
        volatility: "LOW",
      },
      marginBuckets: [
        { label: "TROY wins 1–5", pct: 18.2, tone: "home" },
        { label: "TROY wins 6–13", pct: 10.8, tone: "home" },
        { label: "TROY wins 14+", pct: 2.2, tone: "home" },
        { label: "Tie", pct: 0.0, tone: "neutral" },
        { label: "JSU wins 1–5", pct: 31.5, tone: "away" },
        { label: "JSU wins 6–13", pct: 29.1, tone: "away" },
        { label: "JSU wins 14+", pct: 8.2, tone: "away" },
      ],
      totalDeltaBuckets: [
        { label: "Total -15 to -10", pct: 3.2, tone: "neutral" },
        { label: "Total -10 to -5", pct: 14.4, tone: "neutral" },
        { label: "Total -5 to 0", pct: 33.9, tone: "neutral" },
        { label: "Total 0 to +5", pct: 28.6, tone: "neutral" },
        { label: "Total +5 to +10", pct: 15.1, tone: "neutral" },
        { label: "Total +10 to +15", pct: 4.8, tone: "neutral" },
      ],
      predicted: {
        spread: -1.8, // negative = away favored (JSU)
        total: 41.2,
        score: { home: 19, away: 22 },
      },
    },
    features: {
      "tempo.expected_possessions": 10.6,
      "efficiency.home_eppa": 0.05,
      "efficiency.away_eppa": 0.11,
      "availability.home_impact": 0.71,
      "weather.tax": 0.18,
    },
  },
  {
    id: "nfl-2025-eagles-atl",
    league: "NFL",
    startTimeLocal: "Tonight • 8:15 PM",
    venue: { stadium: "Lincoln Financial Field", city: "Philadelphia", region: "PA" },
    home: { name: "Philadelphia Eagles", short: "PHI", record: "10–4" },
    away: { name: "Atlanta Falcons", short: "ATL", record: "7–7" },
    tags: ["Prime Time", "NFC", "Birds"],

    market: {
      spread: "PHI -4.0",
      total: "O/U 46.0",
      updatedAtLocal: "Updated 6:10 PM",
      lineMoveNote: "Money leaning PHI; total steady.",
    },
    tempo: {
      paceLabel: "AVERAGE",
      tempoScore: 55,
      playsPerGameHome: 64.8,
      playsPerGameAway: 63.2,
      secondsPerPlayHome: 27.1,
      secondsPerPlayAway: 27.8,
    },
    weather: {
      summary: "Breezy — watch downfield efficiency",
      tempF: 43,
      windMph: 16,
      precipChancePct: 10,
      impactScore: 42,
    },
    availability: {
      summary: "Minor question marks; nothing that flips the board",
      impactScore: 28,
      notable: [
        { team: "home", player: "WR2", status: "Probable", note: "Limited reps this week" },
        { team: "away", player: "CB1", status: "Questionable", note: "If out, boosts explosive pass rate" },
      ],
    },
    coaching: { summary: "No changes; both teams consistent in neutral-script pace", impactScore: 15 },
    tldr: {
      headline: "Wind nudges totals — matchup still favors the Birds",
      paragraph:
        "If the wind holds, explosive passing gets taxed and drives become more ‘earned’. That supports a slightly lower total, while Philadelphia’s trench edge keeps them live to cover. Your model should treat wind + pass rate as a multiplier, not a headline.",
      bullets: [
        "Wind impacts explosive passes and kick efficiency",
        "Neutral-script pace suggests average possession count",
        "Availability likely affects ATL coverage depth if CB sits",
      ],
    },
    model: {
      bestBet: {
        spreadLean: "HOME",
        totalLean: "UNDER",
        confidence: "LOW",
        volatility: "MED",
      },
      marginBuckets: [
        { label: "PHI wins 1–3", pct: 17.0, tone: "home" },
        { label: "PHI wins 4–7", pct: 23.5, tone: "home" },
        { label: "PHI wins 8–13", pct: 19.8, tone: "home" },
        { label: "PHI wins 14+", pct: 8.4, tone: "home" },
        { label: "Tie", pct: 1.2, tone: "neutral" },
        { label: "ATL wins 1–3", pct: 12.6, tone: "away" },
        { label: "ATL wins 4–7", pct: 11.1, tone: "away" },
        { label: "ATL wins 8+", pct: 6.4, tone: "away" },
      ],
      totalDeltaBuckets: [
        { label: "Total -12 to -8", pct: 6.4, tone: "neutral" },
        { label: "Total -8 to -4", pct: 18.2, tone: "neutral" },
        { label: "Total -4 to 0", pct: 29.5, tone: "neutral" },
        { label: "Total 0 to +4", pct: 25.1, tone: "neutral" },
        { label: "Total +4 to +8", pct: 14.0, tone: "neutral" },
        { label: "Total +8 to +12", pct: 6.8, tone: "neutral" },
      ],
      predicted: {
        spread: 4.7,
        total: 44.2,
        score: { home: 24, away: 20 },
      },
    },
  },
];

// -----------------------------
// UI helpers
// -----------------------------

function cn(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

function pctFmt(n: number) {
  return `${n.toFixed(2)}%`;
}

function labelToneStyles(tone?: Bucket["tone"]) {
  // Keep it subtle: use theme accents rather than loud team colors.
  // Home gets a "navy" hint, Away gets a "eagle green" hint, neutral stays gray.
  if (tone === "home") return "border-blue-200/40 bg-blue-50/30 text-blue-950";
  if (tone === "away") return "border-emerald-200/40 bg-emerald-50/30 text-emerald-950";
  return "border-slate-200/50 bg-white/30 text-slate-900";
}

function confidenceBadge(c: Model["bestBet"]["confidence"]) {
  if (c === "HIGH") return <Badge className="bg-emerald-600">High</Badge>;
  if (c === "MED") return <Badge className="bg-amber-600">Med</Badge>;
  return <Badge className="bg-slate-600">Low</Badge>;
}

function volatilityBadge(v: Model["bestBet"]["volatility"]) {
  if (v === "LOW") return <Badge className="bg-emerald-600">Low Vol</Badge>;
  if (v === "MED") return <Badge className="bg-amber-600">Med Vol</Badge>;
  return <Badge className="bg-rose-600">High Vol</Badge>;
}

function pickChip(label: string, active: boolean) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold",
        active
          ? "border-slate-900/20 bg-slate-900 text-white"
          : "border-slate-200 bg-white/50 text-slate-700"
      )}
    >
      {label}
    </span>
  );
}

// -----------------------------
// Components
// -----------------------------

function StarStripeBackdrop() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* Navy star field (top-left) */}
      <div className="absolute -left-24 -top-24 h-80 w-80 rounded-[3.5rem] bg-slate-950/95 shadow-2xl" />
      <div className="absolute left-6 top-8 grid grid-cols-9 gap-1 opacity-70">
        {Array.from({ length: 63 }).map((_, i) => (
          <div key={i} className="h-1.5 w-1.5 rounded-full bg-white/85" />
        ))}
      </div>

      {/* Subtle stripes (right) — toned down for desktop readability */}
      <div className="absolute -right-72 top-0 h-[760px] w-[1100px] rotate-6 rounded-[4rem] bg-white/30 shadow-2xl" />
      <div className="absolute -right-72 top-0 h-[760px] w-[1100px] rotate-6 rounded-[4rem] overflow-hidden">
        {Array.from({ length: 12 }).map((_, i) => (
          <div
            key={i}
            className={cn(
              "h-[8.33%]",
              i % 2 === 0 ? "bg-rose-600/20" : "bg-white/10"
            )}
          />
        ))}
      </div>

      {/* Desktop vignette */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-50/10 via-slate-50/10 to-slate-100/40" />
    </div>
  );
}

function AppHeader({ selected }: { selected: GameAnalysisPayload }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <div className="inline-flex items-center gap-2 rounded-2xl bg-white/60 px-3 py-1.5 shadow-sm ring-1 ring-slate-200">
              <Flag className="h-4 w-4" />
              <span className="text-sm font-semibold">Spread Eagle</span>
              <span className="text-xs text-slate-600">• stars & stripes</span>
            </div>
            <Badge variant="secondary" className="bg-white/40">
              {selected.league}
            </Badge>
</div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              {selected.away.short} @ {selected.home.short}
            </h1>
            <span className="text-sm text-slate-600">• {selected.startTimeLocal}</span>
          </div>

          <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-700">
            <MapPin className="h-4 w-4" />
            <span>
              {selected.venue.stadium} • {selected.venue.city}, {selected.venue.region}
            </span>
          </div>
        </div>

        <div className="hidden sm:flex flex-col items-end gap-2">
          <div className="flex items-center gap-2">
            <Badge className="bg-slate-900">{selected.market.spread}</Badge>
            <Badge className="bg-slate-900">{selected.market.total}</Badge>
          </div>
          <div className="text-xs text-slate-600">{selected.market.updatedAtLocal}</div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {selected.tags?.map((t) => (
          <Badge key={t} variant="secondary" className="bg-white/40">
            {t}
          </Badge>
        ))}
        {selected.market.lineMoveNote ? (
          <span className="text-xs text-slate-600">• {selected.market.lineMoveNote}</span>
        ) : null}
      </div>
    </div>
  );
}

function GameList({
  games,
  selectedId,
  onSelect,
}: {
  games: GameAnalysisPayload[];
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  return (
    <Card className="bg-white/50 backdrop-blur-md shadow-sm ring-1 ring-slate-200">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <ClipboardList className="h-4 w-4" />
          Tonight
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        {games.map((g) => {
          const active = g.id === selectedId;
          return (
            <button
              key={g.id}
              onClick={() => onSelect(g.id)}
              className={cn(
                "w-full rounded-2xl border p-3 text-left transition",
                active
                  ? "border-slate-900/20 bg-white shadow-sm"
                  : "border-slate-200 bg-white/30 hover:bg-white/50"
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold">
                    {g.away.short} @ {g.home.short}
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-600">
                    <span>{g.startTimeLocal}</span>
                    <span className="text-slate-400">•</span>
                    <span>{g.market.spread}</span>
                    <span className="text-slate-400">•</span>
                    <span>{g.market.total}</span>
                  </div>
                </div>
                <ArrowRight className={cn("h-4 w-4", active ? "opacity-100" : "opacity-40")} />
              </div>
            </button>
          );
        })}
      </CardContent>
    </Card>
  );
}

function MetricPill({ icon, label, value, sub }: { icon: React.ReactNode; label: string; value: string; sub?: string }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white/50 px-3 py-2">
      <div className="text-slate-900">{icon}</div>
      <div className="leading-tight">
        <div className="text-xs font-semibold text-slate-700">{label}</div>
        <div className="text-sm font-bold text-slate-900">{value}</div>
        {sub ? <div className="text-xs text-slate-600">{sub}</div> : null}
      </div>
    </div>
  );
}

function ScoreAndPick({ g }: { g: GameAnalysisPayload }) {
  const bb = g.model.bestBet;
  const spreadLean = bb.spreadLean;
  const totalLean = bb.totalLean;

  return (
    <Card className="bg-white/50 backdrop-blur-md shadow-sm ring-1 ring-slate-200">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <TrendingUp className="h-4 w-4" />
          Decision
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {confidenceBadge(bb.confidence)}
            {volatilityBadge(bb.volatility)}
          </div>
          <div className="text-xs text-slate-600">
            Model: {g.model.predicted.score.away}–{g.model.predicted.score.home} • Spread {g.model.predicted.spread.toFixed(1)} • Total {g.model.predicted.total.toFixed(1)}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white/60 p-3">
            <div className="text-xs font-semibold text-slate-700">Spread</div>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              {pickChip(`${g.home.short}`, spreadLean === "HOME")}
              {pickChip(`${g.away.short}`, spreadLean === "AWAY")}
              {pickChip("PASS", spreadLean === "PASS")}
            </div>
            <div className="mt-2 text-xs text-slate-600">
              Market: <span className="font-semibold text-slate-900">{g.market.spread}</span>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white/60 p-3">
            <div className="text-xs font-semibold text-slate-700">Total</div>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              {pickChip("OVER", totalLean === "OVER")}
              {pickChip("UNDER", totalLean === "UNDER")}
              {pickChip("PASS", totalLean === "PASS")}
            </div>
            <div className="mt-2 text-xs text-slate-600">
              Market: <span className="font-semibold text-slate-900">{g.market.total}</span>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white/60 p-3">
          <div className="flex items-center justify-between gap-2">
            <div className="text-xs font-semibold text-slate-700">Teaser Readiness</div>
            <Badge variant="secondary" className="bg-white/40">
              {bb.volatility === "LOW" ? "Good" : bb.volatility === "MED" ? "Caution" : "Avoid"}
            </Badge>
          </div>
          <div className="mt-2 text-xs text-slate-600">
            You’ll drive this later from variance + game-state risk. For now: volatility + tempo + availability.
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function TempoDial({ tempo }: { tempo: Tempo }) {
  const v = clamp(tempo.tempoScore, 0, 100);
  const rotation = -90 + (v / 100) * 180; // needle from -90 to +90

  return (
    <Card className="bg-white/50 backdrop-blur-md shadow-sm ring-1 ring-slate-200">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Gauge className="h-4 w-4" />
          Game Tempo
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 sm:grid-cols-[220px_1fr]">
        <div className="flex items-center justify-center">
          <div className="relative h-44 w-44">
            <div className="absolute inset-0 rounded-full border border-slate-200 bg-white/60" />
            <div className="absolute left-1/2 top-1/2 h-1 w-20 -translate-y-1/2 origin-left rounded-full bg-slate-900"
              style={{ transform: `translateY(-50%) rotate(${rotation}deg)` }}
            />
            <div className="absolute left-1/2 top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full bg-slate-900" />
            <div className="absolute inset-x-0 top-6 text-center">
              <div className="text-xs font-semibold text-slate-700">Tempo Score</div>
              <div className="text-2xl font-bold text-slate-900">{v}</div>
              <div className="mt-1 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/60 px-2 py-0.5 text-xs font-semibold">
                <Activity className="h-3.5 w-3.5" /> {tempo.paceLabel}
              </div>
            </div>
            <div className="absolute inset-x-0 bottom-5 text-center text-xs text-slate-600">
              faster pace → more possessions → totals sensitive
            </div>
          </div>
        </div>

        <div className="grid gap-2">
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            <MetricPill
              icon={<Activity className="h-4 w-4" />}
              label="Plays / game"
              value={`${tempo.playsPerGameAway.toFixed(1)} vs ${tempo.playsPerGameHome.toFixed(1)}`}
              sub="Away vs Home"
            />
            <MetricPill
              icon={<ClockIcon />}
              label="Seconds / play"
              value={`${tempo.secondsPerPlayAway.toFixed(1)} vs ${tempo.secondsPerPlayHome.toFixed(1)}`}
              sub="Away vs Home"
            />
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white/60 p-3 text-xs text-slate-700">
            <span className="font-semibold text-slate-900">Interpretation:</span> Pace sets the ceiling for total play volume.
            When tempo is low, underdog run-heavy teams can shrink variance and make spreads tighter.
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ClockIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v6l4 2" />
    </svg>
  );
}

function FactorRow({
  icon,
  title,
  score,
  desc,
}: {
  icon: React.ReactNode;
  title: string;
  score: number;
  desc: string;
}) {
  const v = clamp(score, 0, 100);
  return (
    <div className="rounded-2xl border border-slate-200 bg-white/60 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 text-slate-900">{icon}</div>
          <div>
            <div className="text-sm font-semibold text-slate-900">{title}</div>
            <div className="mt-1 text-xs text-slate-600">{desc}</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs font-semibold text-slate-700">Impact</div>
          <div className="text-lg font-bold text-slate-900">{v}</div>
        </div>
      </div>
      <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-200/70">
        <div className="h-full bg-slate-900" style={{ width: `${v}%` }} />
      </div>
    </div>
  );
}

function KeyFactors({ g }: { g: GameAnalysisPayload }) {
  return (
    <Card className="bg-white/50 backdrop-blur-md shadow-sm ring-1 ring-slate-200">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Shield className="h-4 w-4" />
          Key Factors
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2">
        <FactorRow
          icon={<ThermometerSun className="h-4 w-4" />}
          title="Weather"
          score={g.weather.impactScore}
          desc={`${g.weather.summary} • ${g.weather.tempF}°F • wind ${g.weather.windMph} mph • precip ${g.weather.precipChancePct}%`}
        />
        <FactorRow
          icon={<Users className="h-4 w-4" />}
          title="Availability"
          score={g.availability.impactScore}
          desc={g.availability.summary}
        />
        <FactorRow
          icon={<Stars className="h-4 w-4" />}
          title="Coaching / Scheme"
          score={g.coaching.impactScore}
          desc={g.coaching.summary}
        />

        <div className="rounded-2xl border border-slate-200 bg-white/60 p-3">
          <div className="text-xs font-semibold text-slate-700">Notables</div>
          <div className="mt-2 space-y-2">
            {g.availability.notable.map((n, idx) => (
              <div
                key={idx}
                className={cn(
                  "flex flex-col gap-1 rounded-xl border px-3 py-2",
                  n.team === "home"
                    ? "border-blue-200/40 bg-blue-50/20"
                    : "border-emerald-200/40 bg-emerald-50/20"
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="text-xs font-semibold text-slate-900">{n.player}</div>
                  <Badge variant="secondary" className="bg-white/40">
                    {n.status}
                  </Badge>
                </div>
                <div className="text-xs text-slate-600">{n.note}</div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function DistributionCard({
  title,
  subtitle,
  buckets,
}: {
  title: string;
  subtitle: string;
  buckets: Bucket[];
}) {
  const total = buckets.reduce((a, b) => a + b.pct, 0);
  const max = Math.max(...buckets.map((b) => b.pct), 1);

  return (
    <Card className="bg-white/50 backdrop-blur-md shadow-sm ring-1 ring-slate-200">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Sparkles className="h-4 w-4" />
          {title}
        </CardTitle>
        <div className="text-xs text-slate-600">{subtitle}</div>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="text-xs text-slate-600">
          Sums to <span className="font-semibold text-slate-900">{total.toFixed(2)}%</span>
        </div>
        <Separator />
        <div className="space-y-2">
          {buckets.map((b) => (
            <div
              key={b.label}
              className={cn(
                "rounded-2xl border p-3",
                labelToneStyles(b.tone)
              )}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="text-sm font-semibold">{b.label}</div>
                <div className="text-sm font-bold tabular-nums">{pctFmt(b.pct)}</div>
              </div>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-200/70">
                <div
                  className="h-full bg-slate-900"
                  style={{ width: `${(b.pct / max) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function TLDRCard({ g }: { g: GameAnalysisPayload }) {
  return (
    <Card className="bg-white/50 backdrop-blur-md shadow-sm ring-1 ring-slate-200">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Stars className="h-4 w-4" />
          TL;DR
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="rounded-2xl border border-slate-200 bg-white/60 p-3">
          <div className="text-sm font-semibold text-slate-900">{g.tldr.headline}</div>
          <div className="mt-2 text-sm leading-relaxed text-slate-700">{g.tldr.paragraph}</div>
        </div>

        <div className="grid gap-2 sm:grid-cols-3">
          {g.tldr.bullets.map((x, i) => (
            <div key={i} className="rounded-2xl border border-slate-200 bg-white/60 p-3 text-xs text-slate-700">
              {x}
            </div>
          ))}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white/60 p-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
            <Sparkles className="h-4 w-4" />
            Tone dial (future)
          </div>
          <div className="mt-2 text-xs text-slate-600">
            Later you can switch between: “sharp”, “fun”, “one-liner”, “degenerate”, etc.
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function DataPayloadPreview({ g }: { g: GameAnalysisPayload }) {
  const json = useMemo(() => JSON.stringify(g, null, 2), [g]);
  return (
    <Card className="bg-white/50 backdrop-blur-md shadow-sm ring-1 ring-slate-200">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <CloudRain className="h-4 w-4" />
          Payload Preview
        </CardTitle>
        <div className="text-xs text-slate-600">
          This is the exact shape your backend can produce from Postgres + feature engineering.
        </div>
      </CardHeader>
      <CardContent>
        <pre className="max-h-[520px] overflow-auto rounded-2xl border border-slate-200 bg-slate-950 p-3 text-xs text-slate-100">
          {json}
        </pre>
      </CardContent>
    </Card>
  );
}

// -----------------------------
// Page
// -----------------------------

export default function SpreadEagleMVP() {
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState(mockGames[0].id);

  const games = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return mockGames;
    return mockGames.filter((g) =>
      `${g.away.name} ${g.away.short} ${g.home.name} ${g.home.short} ${g.league}`
        .toLowerCase()
        .includes(q)
    );
  }, [query]);

  const selected = useMemo(() => {
    return mockGames.find((g) => g.id === selectedId) ?? mockGames[0];
  }, [selectedId]);

  return (
    <div className="relative min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      <StarStripeBackdrop />

      <div className="relative mx-auto max-w-7xl px-4 py-6">
        <div className="flex flex-col gap-4">
          <AppHeader selected={selected} />

          <div className="grid gap-4 lg:grid-cols-[340px_1fr]">
            <div className="space-y-4">
              <Card className="bg-white/50 backdrop-blur-md shadow-sm ring-1 ring-slate-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Find a game</CardTitle>
                </CardHeader>
                <CardContent>
                  <Input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search (team / league)"
                    className="bg-white/60"
                  />
                  <div className="mt-3 text-xs text-slate-600">
                    Future: filters (teaser-friendly, low-vol, weather, injuries).
                  </div>
                </CardContent>
              </Card>

              <GameList games={games} selectedId={selectedId} onSelect={setSelectedId} />

              <Card className="bg-white/50 backdrop-blur-md shadow-sm ring-1 ring-slate-200">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <Wind className="h-4 w-4" />
                    Quick Actions
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-2">
                  <Button variant="secondary" className="justify-start bg-white/60">
                    Run analysis (mock)
                  </Button>
                  <Button variant="secondary" className="justify-start bg-white/60">
                    Export card (png/pdf later)
                  </Button>
                  <div className="text-xs text-slate-600">
                    Later: this triggers your pipeline → produces the JSON payload.
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-4">
              <div className="grid gap-4 xl:grid-cols-2">
                <ScoreAndPick g={selected} />
                <TempoDial tempo={selected.tempo} />
              </div>

              <Tabs defaultValue="analysis" className="w-full">
                <TabsList className="bg-white/60">
                  <TabsTrigger value="analysis">Analysis</TabsTrigger>
                  <TabsTrigger value="distributions">Distributions</TabsTrigger>
                  <TabsTrigger value="payload">Payload</TabsTrigger>
                </TabsList>

                <TabsContent value="analysis" className="mt-4 space-y-4">
                  <div className="grid gap-4 xl:grid-cols-2">
                    <TLDRCard g={selected} />
                    <KeyFactors g={selected} />
                  </div>
                </TabsContent>

                <TabsContent value="distributions" className="mt-4 space-y-4">
                  <div className="grid gap-4 xl:grid-cols-2">
                    <DistributionCard
                      title="Margin distribution"
                      subtitle="Blocks add to 100% — your spread decision lives here."
                      buckets={selected.model.marginBuckets}
                    />
                    <DistributionCard
                      title="Total delta distribution"
                      subtitle="Blocks are relative to market total (e.g., -5 to 0)."
                      buckets={selected.model.totalDeltaBuckets}
                    />
                  </div>
                  <Card className="bg-white/50 backdrop-blur-md shadow-sm ring-1 ring-slate-200">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">How to map this to teasers</CardTitle>
                    </CardHeader>
                    <CardContent className="text-sm text-slate-700">
                      <ul className="list-disc space-y-1 pl-5">
                        <li>
                          Use <span className="font-semibold">volatility</span> as a gate.
                        </li>
                        <li>
                          Prefer legs where probability mass is concentrated near the market (tight variance).
                        </li>
                        <li>
                          Later: compute teaser success % directly by integrating these distributions over teased lines.
                        </li>
                      </ul>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="payload" className="mt-4 space-y-4">
                  <DataPayloadPreview g={selected} />
                </TabsContent>
              </Tabs>
            </div>
          </div>

          <footer className="pt-2 text-xs text-slate-600">
            <span className="font-semibold text-slate-900">Spread Eagle</span> • built for desktop • stars + stripes
          </footer>
        </div>
      </div>
    </div>
  );
}
