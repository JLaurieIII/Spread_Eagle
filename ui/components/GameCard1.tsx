"use client";

import React from "react";

/**
 * GameCard1 — Spread Eagle Card 1: Game Context + Betting Snapshot
 *
 * Combines Card 1 (Game Context) and Card 2 (Betting Snapshot) into a single
 * comprehensive game card with patriotic American flag background.
 *
 * Data displayed:
 * - Teams with logos/colors
 * - Venue and game time
 * - Betting lines (spread + total)
 * - Team records (overall, conference, ATS, O/U)
 * - Recent form (W/L dots)
 * - Last 5 games with results
 */

// ============================================================================
// Types
// ============================================================================

type GameResult = {
  date: string;       // e.g., "1/3"
  opponent: string;   // e.g., "Kentucky"
  result: "W" | "L";
  score: string;      // e.g., "87-74"
  spreadResult: number; // e.g., +3 (positive = covered, negative = didn't)
};

type TeamData = {
  name: string;
  shortName: string;
  logo?: string;      // URL or we'll use first letter
  primaryColor: string;
  record: string;     // e.g., "12-6"
  rank?: number;      // e.g., 3 for #3
  confRecord: string; // e.g., "2-3"
  conference: string; // e.g., "SEC"
  atsRecord: string;  // e.g., "6-12"
  ouRecord: string;   // e.g., "12-6"
  recentForm: ("W" | "L")[]; // Last 5 results, most recent last
  last5Games: GameResult[];
};

type GameCard1Props = {
  gameDate: string;      // e.g., "Sat, Jan 24"
  gameTime: string;      // e.g., "8:30pm"
  venue: string;         // e.g., "Coleman Coliseum"
  location: string;      // e.g., "Tuscaloosa, AL"
  spread: string;        // e.g., "ALA -3.5"
  total: string;         // e.g., "167.5"
  homeTeam: TeamData;
  awayTeam: TeamData;
  league?: "NCAA" | "NFL" | "NBA";
};

// ============================================================================
// Sub-components
// ============================================================================

function FlagBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden rounded-2xl">
      {/* Base gradient - warm tan/cream */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#d4c4a8] via-[#c9b896] to-[#bfaf8a]" />

      {/* Stars field (top-left corner) */}
      <div className="absolute -left-4 -top-4 w-48 h-48">
        <div className="absolute inset-0 bg-[#2a3f5f]/90 rounded-br-[80px]" />
        <div className="absolute inset-4 grid grid-cols-6 gap-1.5 p-2">
          {Array.from({ length: 30 }).map((_, i) => (
            <div
              key={i}
              className="w-1.5 h-1.5 bg-white/70 rounded-full"
              style={{ opacity: 0.4 + Math.random() * 0.4 }}
            />
          ))}
        </div>
      </div>

      {/* Stripes - subtle red stripes across */}
      <div className="absolute inset-0 opacity-20">
        {Array.from({ length: 13 }).map((_, i) => (
          <div
            key={i}
            className={`h-[7.69%] ${i % 2 === 0 ? 'bg-[#b22234]' : 'bg-transparent'}`}
          />
        ))}
      </div>

      {/* Vignette overlay for depth */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/10 via-transparent to-white/10" />
      <div className="absolute inset-0 bg-gradient-to-r from-black/5 via-transparent to-black/5" />
    </div>
  );
}

function TeamLogo({ team, side }: { team: TeamData; side: "left" | "right" }) {
  const letter = team.shortName.charAt(0).toUpperCase();

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Logo circle with team color */}
      <div
        className="w-20 h-20 rounded-full flex items-center justify-center shadow-lg"
        style={{
          backgroundColor: team.primaryColor + '15',
          border: `3px solid ${team.primaryColor}40`
        }}
      >
        <span
          className="text-5xl font-black tracking-tight"
          style={{
            color: team.primaryColor,
            fontFamily: "'Georgia', serif",
            textShadow: `2px 2px 4px ${team.primaryColor}30`
          }}
        >
          {letter}
        </span>
      </div>

      {/* Team name */}
      <span
        className="text-xl font-bold tracking-wide"
        style={{
          color: team.primaryColor,
          fontFamily: "'Georgia', serif"
        }}
      >
        {team.name}
      </span>
    </div>
  );
}

function TeamStats({ team, align }: { team: TeamData; align: "left" | "right" }) {
  const alignClass = align === "left" ? "text-left" : "text-right";
  const flexDir = align === "left" ? "flex-row" : "flex-row-reverse";

  return (
    <div className={`flex flex-col gap-1.5 ${alignClass}`}>
      {/* Row 1: Overall record + Rank */}
      <div className={`flex items-baseline gap-3 ${flexDir}`}>
        <span className="text-2xl font-black text-slate-800 tracking-tight">
          {team.record}
        </span>
        {team.rank && (
          <span className="text-lg font-bold text-slate-500">
            {team.rank} OBI3
          </span>
        )}
      </div>

      {/* Row 2: Conference record */}
      <div className={`flex items-center gap-2 ${flexDir}`}>
        <span className="text-lg font-bold text-slate-700">
          {team.confRecord}
        </span>
        <span className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
          {team.conference}
        </span>
      </div>

      {/* Row 3: ATS record */}
      <div className={`flex items-center gap-2 ${flexDir}`}>
        <span className="text-lg font-bold text-slate-700">
          {team.atsRecord}
        </span>
        <span className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
          ATS
        </span>
      </div>

      {/* Row 4: O/U record */}
      <div className={`flex items-center gap-2 ${flexDir}`}>
        <span className="text-lg font-bold text-slate-700">
          {team.ouRecord}
        </span>
        <span className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
          O/U
        </span>
      </div>
    </div>
  );
}

function RecentFormDots({ form, align }: { form: ("W" | "L")[]; align: "left" | "right" }) {
  const justifyClass = align === "left" ? "justify-start" : "justify-end";

  return (
    <div className={`flex items-center gap-1.5 ${justifyClass}`}>
      {form.map((result, i) => (
        <div
          key={i}
          className={`w-3 h-3 rounded-full shadow-sm ${
            result === "W"
              ? "bg-emerald-500 ring-1 ring-emerald-600/30"
              : "bg-red-500 ring-1 ring-red-600/30"
          }`}
        />
      ))}
    </div>
  );
}

function Last5Games({ games, align }: { games: GameResult[]; align: "left" | "right" }) {
  const alignClass = align === "left" ? "text-left" : "text-right";

  return (
    <div className={`flex flex-col gap-0.5 ${alignClass}`}>
      {games.map((game, i) => (
        <div
          key={i}
          className={`text-xs font-medium text-slate-600 flex items-center gap-1 ${
            align === "right" ? "flex-row-reverse" : ""
          }`}
        >
          <span className="text-slate-500 w-8">{game.date}</span>
          <span>{game.opponent}</span>
          <span className={game.result === "W" ? "text-emerald-600 font-bold" : "text-red-600 font-bold"}>
            {game.result}
          </span>
          <span>{game.score}</span>
          <span className={`font-bold ${
            game.spreadResult > 0
              ? "text-emerald-600"
              : game.spreadResult < 0
                ? "text-red-600"
                : "text-slate-500"
          }`}>
            {game.spreadResult > 0 ? "+" : ""}{game.spreadResult}
          </span>
        </div>
      ))}
    </div>
  );
}

function CenterInfo({
  venue,
  location,
  spread,
  total
}: {
  venue: string;
  location: string;
  spread: string;
  total: string;
}) {
  return (
    <div className="flex flex-col items-center gap-3">
      {/* Venue */}
      <div className="flex items-center gap-2 text-slate-600">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <div className="text-center">
          <div className="text-sm font-semibold text-slate-700">{venue}</div>
          <div className="text-xs text-slate-500">{location}</div>
        </div>
      </div>

      {/* Betting lines */}
      <div className="flex items-center gap-2">
        <div className="px-3 py-1.5 bg-[#2a4a7f] text-white text-sm font-bold rounded-md shadow-md">
          {spread}
        </div>
        <div className="px-3 py-1.5 bg-[#2a4a7f] text-white text-sm font-bold rounded-md shadow-md">
          Total {total}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export default function GameCard1({
  gameDate,
  gameTime,
  venue,
  location,
  spread,
  total,
  homeTeam,
  awayTeam,
  league = "NCAA",
}: GameCard1Props) {
  return (
    <div className="relative w-full max-w-4xl rounded-2xl overflow-hidden shadow-2xl">
      <FlagBackground />

      {/* Content */}
      <div className="relative z-10 p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <h1
              className="text-xl font-bold text-slate-800"
              style={{ fontFamily: "'Georgia', serif" }}
            >
              Spread Eagle
            </h1>
            <span className="text-slate-500">•</span>
            <span className="text-lg font-semibold text-slate-600">Card 1</span>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-slate-600">
              {gameDate} • {gameTime}
            </span>
            {league === "NCAA" && (
              <div className="px-2 py-1 bg-slate-800 text-white text-xs font-bold rounded">
                NCAA
              </div>
            )}
          </div>
        </div>

        {/* Main content grid */}
        <div className="grid grid-cols-[1fr_auto_1fr] gap-6 items-start">
          {/* Away team (left) */}
          <div className="flex flex-col items-center gap-4">
            <TeamLogo team={awayTeam} side="left" />
            <TeamStats team={awayTeam} align="left" />
            <RecentFormDots form={awayTeam.recentForm} align="left" />
            <Last5Games games={awayTeam.last5Games} align="left" />
          </div>

          {/* Center - venue and lines */}
          <div className="pt-8">
            <CenterInfo
              venue={venue}
              location={location}
              spread={spread}
              total={total}
            />
          </div>

          {/* Home team (right) */}
          <div className="flex flex-col items-center gap-4">
            <TeamLogo team={homeTeam} side="right" />
            <TeamStats team={homeTeam} align="right" />
            <RecentFormDots form={homeTeam.recentForm} align="right" />
            <Last5Games games={homeTeam.last5Games} align="right" />
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Demo/Preview Data
// ============================================================================

export const demoGameData: GameCard1Props = {
  gameDate: "Sat, Jan 24",
  gameTime: "8:30pm",
  venue: "Coleman Coliseum",
  location: "Tuscaloosa, AL",
  spread: "ALA -3.5",
  total: "167.5",
  awayTeam: {
    name: "Tennessee",
    shortName: "TENN",
    primaryColor: "#FF8200", // Tennessee Orange
    record: "12-6",
    rank: 1,
    confRecord: "2-3",
    conference: "SEC",
    atsRecord: "6-12",
    ouRecord: "12-6",
    recentForm: ["W", "L", "W", "W", "L"],
    last5Games: [
      { date: "1/3", opponent: "Kentucky", result: "W", score: "87-74", spreadResult: 3 },
      { date: "1/6", opponent: "Auburn", result: "L", score: "72-80", spreadResult: -4 },
      { date: "1/10", opponent: "Florida", result: "W", score: "79-71", spreadResult: -2 },
      { date: "1/14", opponent: "LSU", result: "W", score: "82-68", spreadResult: -6 },
      { date: "1/18", opponent: "Arkansas", result: "L", score: "74-78", spreadResult: 1.5 },
    ],
  },
  homeTeam: {
    name: "Alabama",
    shortName: "ALA",
    primaryColor: "#9E1B32", // Alabama Crimson
    record: "13-5",
    rank: 3,
    confRecord: "3-2",
    conference: "SEC",
    atsRecord: "7-10",
    ouRecord: "9-8",
    recentForm: ["W", "L", "L", "W", "L"],
    last5Games: [
      { date: "1/3", opponent: "Kentucky", result: "W", score: "87-74", spreadResult: 3 },
      { date: "1/7", opponent: "Ole Miss", result: "W", score: "91-85", spreadResult: -2 },
      { date: "1/11", opponent: "Missouri", result: "L", score: "88-92", spreadResult: -5 },
      { date: "1/15", opponent: "Georgia", result: "W", score: "95-83", spreadResult: -7 },
      { date: "1/19", opponent: "Texas A&M", result: "L", score: "80-86", spreadResult: 1 },
    ],
  },
};
