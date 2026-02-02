"use client";

import React, { useState } from "react";

/**
 * SPREAD EAGLE - MOBILE-FIRST EDITION
 *
 * Design Direction: Optimized for phone screens with swipe interactions
 * - Card-based navigation
 * - Large touch targets
 * - Bottom navigation
 * - Swipeable team comparison
 * - Compact but readable data visualization
 */

// Mock data
const MOCK_GAMES = [
  {
    id: 1,
    gameTime: "7:00 PM",
    spread: "-7.5",
    total: "147.5",
    homeTeam: {
      name: "Kansas",
      fullName: "Kansas Jayhawks",
      primaryColor: "#0051BA",
      record: "18-3",
      rank: 4,
      atsRecord: "12-9",
      recentForm: ["W", "W", "L", "W", "W"] as ("W" | "L")[],
      predictability: 68,
    },
    awayTeam: {
      name: "Baylor",
      fullName: "Baylor Bears",
      primaryColor: "#154734",
      record: "15-6",
      rank: 12,
      atsRecord: "13-8",
      recentForm: ["L", "W", "W", "L", "W"] as ("W" | "L")[],
      predictability: 65,
    },
    eagleScore: 71,
    verdict: "STRONG PLAY",
  },
  {
    id: 2,
    gameTime: "9:00 PM",
    spread: "-3.5",
    total: "142.0",
    homeTeam: {
      name: "Duke",
      fullName: "Duke Blue Devils",
      primaryColor: "#003087",
      record: "17-4",
      rank: 6,
      atsRecord: "10-11",
      recentForm: ["W", "L", "W", "W", "W"] as ("W" | "L")[],
      predictability: 72,
    },
    awayTeam: {
      name: "UNC",
      fullName: "North Carolina Tar Heels",
      primaryColor: "#7BAFD4",
      record: "14-7",
      rank: 18,
      atsRecord: "11-10",
      recentForm: ["W", "W", "L", "W", "L"] as ("W" | "L")[],
      predictability: 58,
    },
    eagleScore: 65,
    verdict: "MODERATE",
  },
];

// Mobile game card
function MobileGameCard({
  game,
  isSelected,
  onSelect,
}: {
  game: typeof MOCK_GAMES[0];
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      className="w-full text-left transition-all duration-200"
      style={{
        transform: isSelected ? "scale(1)" : "scale(0.98)",
        opacity: isSelected ? 1 : 0.7
      }}
    >
      <div
        className="rounded-2xl overflow-hidden"
        style={{
          background: isSelected
            ? `linear-gradient(135deg, ${game.awayTeam.primaryColor}20, ${game.homeTeam.primaryColor}20)`
            : "rgba(30, 41, 59, 0.5)",
          border: isSelected ? `2px solid ${game.homeTeam.primaryColor}60` : "2px solid transparent"
        }}
      >
        <div className="p-4">
          {/* Teams */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center font-bold text-white text-sm"
                style={{ background: game.awayTeam.primaryColor }}
              >
                {game.awayTeam.name.substring(0, 3).toUpperCase()}
              </div>
              <div>
                <div className="text-white font-semibold">{game.awayTeam.name}</div>
                <div className="text-slate-400 text-xs">{game.awayTeam.record}</div>
              </div>
            </div>
            <div className="text-slate-400 text-sm font-medium">@</div>
            <div className="flex items-center gap-3 flex-row-reverse">
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center font-bold text-white text-sm"
                style={{ background: game.homeTeam.primaryColor }}
              >
                {game.homeTeam.name.substring(0, 3).toUpperCase()}
              </div>
              <div className="text-right">
                <div className="text-white font-semibold">{game.homeTeam.name}</div>
                <div className="text-slate-400 text-xs">{game.homeTeam.record}</div>
              </div>
            </div>
          </div>

          {/* Lines and score */}
          <div className="flex items-center justify-between pt-3 border-t border-slate-700/50">
            <div className="flex gap-4">
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Spread</div>
                <div className="text-white font-semibold">{game.spread}</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Total</div>
                <div className="text-white font-semibold">{game.total}</div>
              </div>
            </div>
            <div className="text-right">
              <div
                className="text-2xl font-black"
                style={{
                  color: game.eagleScore >= 70 ? "#22c55e" : game.eagleScore >= 60 ? "#eab308" : "#ef4444"
                }}
              >
                {game.eagleScore}
              </div>
              <div className="text-[10px] text-slate-500 uppercase">{game.verdict}</div>
            </div>
          </div>
        </div>
      </div>
    </button>
  );
}

// Mobile team detail
function MobileTeamDetail({ team, isHome }: { team: typeof MOCK_GAMES[0]["homeTeam"]; isHome: boolean }) {
  return (
    <div
      className="rounded-2xl p-5"
      style={{
        background: `linear-gradient(135deg, ${team.primaryColor}30, ${team.primaryColor}10)`,
        border: `1px solid ${team.primaryColor}40`
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center font-bold text-white"
            style={{ background: team.primaryColor }}
          >
            {team.name.charAt(0)}
          </div>
          <div>
            <div className="text-white font-bold text-lg">{team.fullName}</div>
            <div className="text-slate-400 text-sm">
              {team.rank && `#${team.rank} • `}{team.record}
            </div>
          </div>
        </div>
        <span
          className="text-xs px-2 py-1 rounded font-medium"
          style={{
            background: isHome ? "rgba(34, 197, 94, 0.2)" : "rgba(239, 68, 68, 0.2)",
            color: isHome ? "#22c55e" : "#ef4444"
          }}
        >
          {isHome ? "HOME" : "AWAY"}
        </span>
      </div>

      {/* Stats row */}
      <div className="flex justify-between mb-4">
        <div>
          <div className="text-[10px] text-slate-500 uppercase">ATS</div>
          <div className="text-white font-semibold">{team.atsRecord}</div>
        </div>
        <div className="text-right">
          <div className="text-[10px] text-slate-500 uppercase">Predictability</div>
          <div
            className="text-lg font-bold"
            style={{
              color: team.predictability >= 65 ? "#22c55e" : team.predictability >= 55 ? "#eab308" : "#ef4444"
            }}
          >
            {team.predictability}%
          </div>
        </div>
      </div>

      {/* Recent form */}
      <div>
        <div className="text-[10px] text-slate-500 uppercase mb-2">Last 5</div>
        <div className="flex gap-1.5">
          {team.recentForm.map((result, i) => (
            <div
              key={i}
              className="flex-1 h-8 rounded flex items-center justify-center font-bold text-sm"
              style={{
                background: result === "W" ? "rgba(34, 197, 94, 0.2)" : "rgba(239, 68, 68, 0.2)",
                color: result === "W" ? "#22c55e" : "#ef4444"
              }}
            >
              {result}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function MobileFirstDesign() {
  const [selectedGameId, setSelectedGameId] = useState(MOCK_GAMES[0].id);
  const [activeTab, setActiveTab] = useState<"games" | "detail">("games");

  const selectedGame = MOCK_GAMES.find(g => g.id === selectedGameId)!;

  return (
    <div
      className="min-h-screen pb-20"
      style={{
        background: "linear-gradient(180deg, #0f172a 0%, #1e293b 100%)",
        fontFamily: "'Inter', -apple-system, sans-serif",
        maxWidth: "430px",
        margin: "0 auto"
      }}
    >
      {/* Status bar mock */}
      <div className="h-12 flex items-center justify-between px-6 text-white text-sm">
        <span>9:41</span>
        <div className="flex items-center gap-1">
          <span>📶</span>
          <span>🔋</span>
        </div>
      </div>

      {/* Header */}
      <header className="px-5 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img
              src="/logo.jpeg"
              alt="Spread Eagle"
              className="w-10 h-10 rounded-xl"
            />
            <div>
              <h1 className="text-white font-bold text-lg">Spread Eagle</h1>
              <p className="text-slate-400 text-xs">Feb 1, 2025</p>
            </div>
          </div>
          <button className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-slate-400">
            ⚙️
          </button>
        </div>
      </header>

      {/* Tab switcher */}
      <div className="px-5 mb-4">
        <div className="flex gap-2 p-1 rounded-xl bg-slate-800/50">
          <button
            onClick={() => setActiveTab("games")}
            className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === "games"
                ? "bg-white text-slate-900"
                : "text-slate-400"
            }`}
          >
            Games ({MOCK_GAMES.length})
          </button>
          <button
            onClick={() => setActiveTab("detail")}
            className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === "detail"
                ? "bg-white text-slate-900"
                : "text-slate-400"
            }`}
          >
            Analysis
          </button>
        </div>
      </div>

      {/* Content */}
      <main className="px-5">
        {activeTab === "games" ? (
          <div className="space-y-3">
            {MOCK_GAMES.map((game) => (
              <MobileGameCard
                key={game.id}
                game={game}
                isSelected={game.id === selectedGameId}
                onSelect={() => {
                  setSelectedGameId(game.id);
                  setActiveTab("detail");
                }}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Eagle score banner */}
            <div
              className="rounded-2xl p-5 text-center"
              style={{
                background: selectedGame.eagleScore >= 70
                  ? "linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(34, 197, 94, 0.05))"
                  : "linear-gradient(135deg, rgba(234, 179, 8, 0.2), rgba(234, 179, 8, 0.05))",
                border: `1px solid ${selectedGame.eagleScore >= 70 ? "rgba(34, 197, 94, 0.3)" : "rgba(234, 179, 8, 0.3)"}`
              }}
            >
              <div className="text-slate-400 text-xs uppercase tracking-wider mb-1">Eagle Score</div>
              <div
                className="text-5xl font-black mb-1"
                style={{
                  color: selectedGame.eagleScore >= 70 ? "#22c55e" : "#eab308"
                }}
              >
                {selectedGame.eagleScore}
              </div>
              <div
                className="text-sm font-semibold uppercase tracking-wider"
                style={{
                  color: selectedGame.eagleScore >= 70 ? "#22c55e" : "#eab308"
                }}
              >
                {selectedGame.verdict}
              </div>
            </div>

            {/* Lines */}
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl p-4 bg-slate-800/50 text-center">
                <div className="text-slate-400 text-xs uppercase mb-1">Spread</div>
                <div className="text-white text-2xl font-bold">{selectedGame.spread}</div>
              </div>
              <div className="rounded-xl p-4 bg-slate-800/50 text-center">
                <div className="text-slate-400 text-xs uppercase mb-1">Total</div>
                <div className="text-white text-2xl font-bold">{selectedGame.total}</div>
              </div>
            </div>

            {/* Team details */}
            <MobileTeamDetail team={selectedGame.awayTeam} isHome={false} />
            <MobileTeamDetail team={selectedGame.homeTeam} isHome={true} />
          </div>
        )}
      </main>

      {/* Bottom navigation */}
      <nav
        className="fixed bottom-0 left-0 right-0 h-20 flex items-center justify-around px-6 border-t border-slate-800"
        style={{
          background: "rgba(15, 23, 42, 0.95)",
          backdropFilter: "blur(10px)",
          maxWidth: "430px",
          margin: "0 auto"
        }}
      >
        <button className="flex flex-col items-center gap-1 text-white">
          <span className="text-xl">🏀</span>
          <span className="text-[10px] font-medium">Games</span>
        </button>
        <button className="flex flex-col items-center gap-1 text-slate-500">
          <span className="text-xl">📊</span>
          <span className="text-[10px] font-medium">Trends</span>
        </button>
        <button className="flex flex-col items-center gap-1 text-slate-500">
          <span className="text-xl">⭐</span>
          <span className="text-[10px] font-medium">Picks</span>
        </button>
        <button className="flex flex-col items-center gap-1 text-slate-500">
          <span className="text-xl">👤</span>
          <span className="text-[10px] font-medium">Profile</span>
        </button>
      </nav>
    </div>
  );
}
