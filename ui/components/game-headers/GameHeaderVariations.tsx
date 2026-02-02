"use client";

import React from "react";
import { MapPin, Clock } from "lucide-react";

/**
 * GAME HEADER DESIGN VARIATIONS
 *
 * 4 distinct styles for the Spread Eagle game matchup header.
 * Each can be dropped into the GameDetailDashboard component.
 */

// Props interface matching the existing game data
interface GameHeaderProps {
  game: {
    awayTeam: {
      shortName: string;
      name: string;
      primaryColor: string;
      secondaryColor: string;
      conference: string;
      rank?: number | null;
    };
    homeTeam: {
      shortName: string;
      name: string;
      primaryColor: string;
      secondaryColor: string;
      conference: string;
      rank?: number | null;
    };
    venue: string;
    location: string;
    gameDate: string;
    gameTime: string;
    spread: string | null;
    total: string | null;
    spreadEagleScore: number | null;
    spreadEagleVerdict: string;
  };
}

// ============================================================================
// VARIATION 1: "SCOREBOARD" - Classic stadium scoreboard aesthetic
// ============================================================================
export function GameHeaderScoreboard({ game }: GameHeaderProps) {
  return (
    <div
      className="relative rounded-2xl overflow-hidden"
      style={{
        background: "linear-gradient(180deg, #0A1628 0%, #152238 100%)",
        boxShadow: "0 4px 30px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)"
      }}
    >
      {/* Top accent line */}
      <div className="h-1 flex">
        <div className="flex-1" style={{ background: game.awayTeam.primaryColor }} />
        <div className="flex-1" style={{ background: game.homeTeam.primaryColor }} />
      </div>

      <div className="p-6">
        {/* Main matchup row */}
        <div className="flex items-center justify-between mb-6">
          {/* Away team */}
          <div className="flex items-center gap-4">
            <div
              className="w-16 h-16 rounded-xl flex items-center justify-center text-2xl font-black"
              style={{
                background: game.awayTeam.primaryColor,
                color: "#fff",
                boxShadow: `0 4px 20px ${game.awayTeam.primaryColor}50`
              }}
            >
              {game.awayTeam.shortName.substring(0, 3).toUpperCase()}
            </div>
            <div>
              {game.awayTeam.rank && (
                <span className="text-xs font-bold text-slate-400">#{game.awayTeam.rank}</span>
              )}
              <div className="text-xl font-bold text-white">{game.awayTeam.name}</div>
              <div className="text-xs text-slate-500">{game.awayTeam.conference}</div>
            </div>
          </div>

          {/* Center - VS and lines */}
          <div className="flex flex-col items-center gap-2">
            <span className="text-2xl font-black text-slate-600">@</span>
            <div className="flex gap-3">
              {game.spread && (
                <div
                  className="px-4 py-2 rounded-lg text-center"
                  style={{ background: "rgba(255,255,255,0.1)" }}
                >
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">Spread</div>
                  <div className="text-xl font-black text-white">{game.spread}</div>
                </div>
              )}
              {game.total && (
                <div
                  className="px-4 py-2 rounded-lg text-center"
                  style={{ background: "rgba(255,255,255,0.1)" }}
                >
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">Total</div>
                  <div className="text-xl font-black text-white">{game.total}</div>
                </div>
              )}
            </div>
          </div>

          {/* Home team */}
          <div className="flex items-center gap-4 flex-row-reverse">
            <div
              className="w-16 h-16 rounded-xl flex items-center justify-center text-2xl font-black"
              style={{
                background: game.homeTeam.primaryColor,
                color: "#fff",
                boxShadow: `0 4px 20px ${game.homeTeam.primaryColor}50`
              }}
            >
              {game.homeTeam.shortName.substring(0, 3).toUpperCase()}
            </div>
            <div className="text-right">
              {game.homeTeam.rank && (
                <span className="text-xs font-bold text-slate-400">#{game.homeTeam.rank}</span>
              )}
              <div className="text-xl font-bold text-white">{game.homeTeam.name}</div>
              <div className="text-xs text-slate-500">{game.homeTeam.conference}</div>
            </div>
          </div>
        </div>

        {/* Bottom info bar */}
        <div
          className="flex items-center justify-between pt-4 border-t"
          style={{ borderColor: "rgba(255,255,255,0.1)" }}
        >
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <span className="flex items-center gap-1.5">
              <MapPin className="w-4 h-4" />
              {game.venue}
            </span>
            <span className="flex items-center gap-1.5">
              <Clock className="w-4 h-4" />
              {game.gameTime}
            </span>
          </div>
          {game.spreadEagleVerdict && game.spreadEagleVerdict !== "N/A" && (
            <div
              className="px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider"
              style={{
                background: game.spreadEagleVerdict === "SPREAD EAGLE"
                  ? "rgba(34, 197, 94, 0.2)"
                  : "rgba(251, 191, 36, 0.2)",
                color: game.spreadEagleVerdict === "SPREAD EAGLE" ? "#4ade80" : "#fbbf24"
              }}
            >
              {game.spreadEagleVerdict} {game.spreadEagleScore && `(${game.spreadEagleScore})`}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// VARIATION 2: "TICKET STUB" - Vintage sports ticket aesthetic
// ============================================================================
export function GameHeaderTicket({ game }: GameHeaderProps) {
  return (
    <div className="relative">
      {/* Perforated edge effect */}
      <div className="absolute left-0 top-0 bottom-0 w-4 flex flex-col justify-around">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="w-4 h-4 rounded-full bg-slate-100" style={{ marginLeft: "-8px" }} />
        ))}
      </div>
      <div className="absolute right-0 top-0 bottom-0 w-4 flex flex-col justify-around">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="w-4 h-4 rounded-full bg-slate-100" style={{ marginRight: "-8px" }} />
        ))}
      </div>

      <div
        className="relative ml-2 mr-2 rounded-lg overflow-hidden"
        style={{
          background: "#faf9f6",
          border: "2px dashed #d4d0c8"
        }}
      >
        {/* Header strip */}
        <div
          className="px-6 py-3 text-center"
          style={{ background: "#0f2557" }}
        >
          <span
            className="text-xs font-bold tracking-[0.4em] uppercase"
            style={{ color: "#94a3b8" }}
          >
            Admit One • College Basketball
          </span>
        </div>

        <div className="p-6">
          {/* Teams */}
          <div className="flex items-center justify-center gap-6 mb-6">
            <div className="text-right">
              {game.awayTeam.rank && (
                <span className="text-xs font-semibold" style={{ color: "#64748b" }}>#{game.awayTeam.rank}</span>
              )}
              <div
                className="text-2xl font-black uppercase"
                style={{
                  color: game.awayTeam.primaryColor,
                  fontFamily: "var(--font-oswald), 'Oswald', sans-serif"
                }}
              >
                {game.awayTeam.shortName}
              </div>
            </div>

            <div
              className="text-3xl font-black"
              style={{ color: "#0f2557" }}
            >
              VS
            </div>

            <div className="text-left">
              {game.homeTeam.rank && (
                <span className="text-xs font-semibold" style={{ color: "#64748b" }}>#{game.homeTeam.rank}</span>
              )}
              <div
                className="text-2xl font-black uppercase"
                style={{
                  color: game.homeTeam.primaryColor,
                  fontFamily: "var(--font-oswald), 'Oswald', sans-serif"
                }}
              >
                {game.homeTeam.shortName}
              </div>
            </div>
          </div>

          {/* Betting lines - styled like ticket price */}
          <div className="flex justify-center gap-4 mb-6">
            {game.spread && (
              <div
                className="px-6 py-3 rounded-lg text-center"
                style={{
                  background: "#0f2557",
                  transform: "rotate(-1deg)"
                }}
              >
                <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Line</div>
                <div
                  className="text-3xl font-black text-white"
                  style={{ fontFamily: "var(--font-oswald), 'Oswald', sans-serif" }}
                >
                  {game.spread}
                </div>
              </div>
            )}
            {game.total && (
              <div
                className="px-6 py-3 rounded-lg text-center"
                style={{
                  background: "#B91C1C",
                  transform: "rotate(1deg)"
                }}
              >
                <div className="text-[10px] text-red-200 uppercase tracking-wider mb-1">Total</div>
                <div
                  className="text-3xl font-black text-white"
                  style={{ fontFamily: "var(--font-oswald), 'Oswald', sans-serif" }}
                >
                  {game.total}
                </div>
              </div>
            )}
          </div>

          {/* Venue and time */}
          <div
            className="flex items-center justify-between pt-4 border-t-2 border-dashed"
            style={{ borderColor: "#d4d0c8" }}
          >
            <div className="text-sm" style={{ color: "#64748b" }}>
              <div className="font-semibold">{game.venue}</div>
              <div>{game.location}</div>
            </div>
            <div className="text-right text-sm" style={{ color: "#64748b" }}>
              <div className="font-semibold">{game.gameDate}</div>
              <div>{game.gameTime}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// VARIATION 3: "BROADCAST" - ESPN/Fox Sports lower-third style
// ============================================================================
export function GameHeaderBroadcast({ game }: GameHeaderProps) {
  return (
    <div className="relative">
      {/* Main container with diagonal cut */}
      <div
        className="relative rounded-xl overflow-hidden"
        style={{ background: "#0A1628" }}
      >
        {/* Diagonal team color backgrounds */}
        <div className="absolute inset-0 flex">
          <div
            className="w-1/2 h-full"
            style={{
              background: `linear-gradient(135deg, ${game.awayTeam.primaryColor}40 0%, transparent 70%)`
            }}
          />
          <div
            className="w-1/2 h-full"
            style={{
              background: `linear-gradient(-135deg, ${game.homeTeam.primaryColor}40 0%, transparent 70%)`
            }}
          />
        </div>

        <div className="relative p-5">
          {/* Top bar - Live indicator style */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                College Basketball
              </span>
            </div>
            <div className="text-xs text-slate-500">
              {game.gameDate} • {game.gameTime}
            </div>
          </div>

          {/* Main matchup - broadcast style */}
          <div className="flex items-stretch gap-4">
            {/* Away team panel */}
            <div
              className="flex-1 p-4 rounded-lg"
              style={{
                background: `linear-gradient(135deg, ${game.awayTeam.primaryColor} 0%, ${game.awayTeam.primaryColor}cc 100%)`,
                clipPath: "polygon(0 0, 100% 0, 95% 100%, 0 100%)"
              }}
            >
              <div className="flex items-center gap-3">
                {game.awayTeam.rank && (
                  <span className="text-xs font-bold text-white/70">#{game.awayTeam.rank}</span>
                )}
                <span
                  className="text-2xl font-black text-white uppercase tracking-tight"
                  style={{ fontFamily: "var(--font-oswald), sans-serif" }}
                >
                  {game.awayTeam.shortName}
                </span>
              </div>
              <div className="text-xs text-white/60 mt-1">{game.awayTeam.conference}</div>
            </div>

            {/* Center - betting lines */}
            <div className="flex flex-col justify-center items-center gap-2 px-4">
              <div
                className="px-4 py-2 rounded text-center transform -skew-x-6"
                style={{ background: "rgba(255,255,255,0.15)" }}
              >
                <div className="transform skew-x-6">
                  <div className="text-[9px] text-slate-400 uppercase tracking-wider">Spread</div>
                  <div className="text-2xl font-black text-white">{game.spread || "TBD"}</div>
                </div>
              </div>
              <div
                className="px-4 py-2 rounded text-center transform -skew-x-6"
                style={{ background: "rgba(255,255,255,0.15)" }}
              >
                <div className="transform skew-x-6">
                  <div className="text-[9px] text-slate-400 uppercase tracking-wider">O/U</div>
                  <div className="text-2xl font-black text-white">{game.total || "TBD"}</div>
                </div>
              </div>
            </div>

            {/* Home team panel */}
            <div
              className="flex-1 p-4 rounded-lg text-right"
              style={{
                background: `linear-gradient(-135deg, ${game.homeTeam.primaryColor} 0%, ${game.homeTeam.primaryColor}cc 100%)`,
                clipPath: "polygon(5% 0, 100% 0, 100% 100%, 0 100%)"
              }}
            >
              <div className="flex items-center gap-3 justify-end">
                <span
                  className="text-2xl font-black text-white uppercase tracking-tight"
                  style={{ fontFamily: "var(--font-oswald), sans-serif" }}
                >
                  {game.homeTeam.shortName}
                </span>
                {game.homeTeam.rank && (
                  <span className="text-xs font-bold text-white/70">#{game.homeTeam.rank}</span>
                )}
              </div>
              <div className="text-xs text-white/60 mt-1">{game.homeTeam.conference}</div>
            </div>
          </div>

          {/* Bottom ticker */}
          <div
            className="flex items-center justify-between mt-4 pt-3 border-t"
            style={{ borderColor: "rgba(255,255,255,0.1)" }}
          >
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <MapPin className="w-3 h-3" />
              <span>{game.venue}</span>
            </div>
            {game.spreadEagleVerdict && game.spreadEagleVerdict !== "N/A" && (
              <div
                className="px-3 py-1 rounded transform -skew-x-6 text-xs font-bold uppercase"
                style={{
                  background: game.spreadEagleVerdict === "SPREAD EAGLE" ? "#22c55e" : "#f59e0b",
                  color: "#000"
                }}
              >
                <span className="transform skew-x-6 inline-block">
                  {game.spreadEagleVerdict}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// VARIATION 4: "MINIMAL EDITORIAL" - Clean magazine/editorial style
// ============================================================================
export function GameHeaderEditorial({ game }: GameHeaderProps) {
  return (
    <div
      className="relative rounded-2xl p-8"
      style={{
        background: "#ffffff",
        boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 8px 30px rgba(0,0,0,0.05)"
      }}
    >
      {/* Minimal top accent */}
      <div className="flex gap-1 mb-6">
        <div className="h-1 w-12 rounded-full" style={{ background: game.awayTeam.primaryColor }} />
        <div className="h-1 w-12 rounded-full" style={{ background: game.homeTeam.primaryColor }} />
      </div>

      {/* Main content */}
      <div className="flex items-start justify-between">
        {/* Left - Matchup */}
        <div>
          <div className="text-xs font-medium text-slate-400 uppercase tracking-widest mb-3">
            {game.awayTeam.conference} × {game.homeTeam.conference}
          </div>

          <div className="flex items-baseline gap-4 mb-2">
            <span
              className="text-4xl font-black uppercase tracking-tight"
              style={{
                color: game.awayTeam.primaryColor,
                fontFamily: "var(--font-oswald), 'Oswald', serif"
              }}
            >
              {game.awayTeam.rank && <sup className="text-lg text-slate-400 mr-1">#{game.awayTeam.rank}</sup>}
              {game.awayTeam.shortName}
            </span>
            <span className="text-2xl text-slate-300">at</span>
            <span
              className="text-4xl font-black uppercase tracking-tight"
              style={{
                color: game.homeTeam.primaryColor,
                fontFamily: "var(--font-oswald), 'Oswald', serif"
              }}
            >
              {game.homeTeam.rank && <sup className="text-lg text-slate-400 mr-1">#{game.homeTeam.rank}</sup>}
              {game.homeTeam.shortName}
            </span>
          </div>

          <div className="flex items-center gap-4 text-sm text-slate-500">
            <span>{game.venue}</span>
            <span className="w-1 h-1 rounded-full bg-slate-300" />
            <span>{game.gameDate}</span>
            <span className="w-1 h-1 rounded-full bg-slate-300" />
            <span>{game.gameTime}</span>
          </div>
        </div>

        {/* Right - Lines */}
        <div className="flex items-start gap-6">
          {game.spread && (
            <div className="text-center">
              <div
                className="text-4xl font-black"
                style={{
                  color: "#0f2557",
                  fontFamily: "var(--font-oswald), 'Oswald', sans-serif"
                }}
              >
                {game.spread}
              </div>
              <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mt-1">
                Spread
              </div>
            </div>
          )}

          <div className="w-px h-12 bg-slate-200" />

          {game.total && (
            <div className="text-center">
              <div
                className="text-4xl font-black"
                style={{
                  color: "#0f2557",
                  fontFamily: "var(--font-oswald), 'Oswald', sans-serif"
                }}
              >
                {game.total}
              </div>
              <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mt-1">
                Total
              </div>
            </div>
          )}

          {game.spreadEagleScore && (
            <>
              <div className="w-px h-12 bg-slate-200" />
              <div className="text-center">
                <div
                  className="text-4xl font-black"
                  style={{
                    color: game.spreadEagleVerdict === "SPREAD EAGLE" ? "#16a34a" : "#d97706",
                    fontFamily: "var(--font-oswald), 'Oswald', sans-serif"
                  }}
                >
                  {game.spreadEagleScore}
                </div>
                <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mt-1">
                  Eagle
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// DEFAULT EXPORT - All variations for easy preview
// ============================================================================
export default function GameHeaderShowcase({ game }: GameHeaderProps) {
  return (
    <div className="space-y-8 p-8 bg-slate-100 min-h-screen">
      <h2 className="text-2xl font-bold text-slate-800 mb-4">Game Header Variations</h2>

      <div>
        <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">1. Scoreboard Style</h3>
        <GameHeaderScoreboard game={game} />
      </div>

      <div>
        <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">2. Ticket Stub Style</h3>
        <GameHeaderTicket game={game} />
      </div>

      <div>
        <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">3. Broadcast Style</h3>
        <GameHeaderBroadcast game={game} />
      </div>

      <div>
        <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">4. Editorial Style</h3>
        <GameHeaderEditorial game={game} />
      </div>
    </div>
  );
}
