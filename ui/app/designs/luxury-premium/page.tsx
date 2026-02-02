"use client";

import React from "react";

/**
 * SPREAD EAGLE - LUXURY PREMIUM EDITION
 *
 * Design Direction: High-end sportsbook / VIP lounge aesthetic
 * - Rich blacks with champagne gold accents
 * - Velvet textures and subtle noise overlays
 * - Elegant serif typography for headlines
 * - Team colors as jewel-tone accents
 * - Card-based layout with premium shadows
 * - Art deco geometric patterns
 */

// Mock data
const MOCK_GAME = {
  id: 1,
  gameDate: "2025-02-01",
  gameTime: "7:00 PM ET",
  venue: "Allen Fieldhouse",
  location: "Lawrence, KS",
  spread: "-7.5",
  total: "147.5",
  homeTeam: {
    name: "Kansas Jayhawks",
    shortName: "Kansas",
    primaryColor: "#0051BA",
    secondaryColor: "#E8000D",
    record: "18-3",
    rank: 4,
    confRecord: "8-2",
    conference: "Big 12",
    atsRecord: "12-9",
    ouRecord: "11-10",
    recentForm: ["W", "W", "L", "W", "W"] as ("W" | "L")[],
    spreadDistribution: {
      margins: [-2, 5, -8, 12, 3, -4, 7, 15, -1, 6, 2, -5, 9, 4, -3],
      mean: 2.8,
      std: 6.2,
      predictability: 68,
    },
  },
  awayTeam: {
    name: "Baylor Bears",
    shortName: "Baylor",
    primaryColor: "#154734",
    secondaryColor: "#FFB81C",
    record: "15-6",
    rank: 12,
    confRecord: "6-4",
    conference: "Big 12",
    atsRecord: "13-8",
    ouRecord: "9-12",
    recentForm: ["L", "W", "W", "L", "W"] as ("W" | "L")[],
    spreadDistribution: {
      margins: [4, -7, 2, 9, -3, 5, -11, 3, 8, -2, 6, 1, -4, 7, 2],
      mean: 1.3,
      std: 5.8,
      predictability: 65,
    },
  },
  spreadPredictability: 66,
  totalPredictability: 73,
  spreadEagleScore: 71,
  spreadEagleVerdict: "STRONG PLAY",
};

// Elegant KDE with gold accents
function LuxuryKDE({
  margins,
  mean,
  std,
  predictability,
}: {
  margins: number[];
  mean: number;
  std: number;
  predictability: number;
}) {
  const bandwidth = std * 0.5 || 5;
  const xMin = -25;
  const xMax = 25;
  const points = 50;
  const xValues = Array.from({ length: points }, (_, i) => xMin + (i * (xMax - xMin)) / (points - 1));

  const gaussian = (x: number, xi: number) =>
    Math.exp(-0.5 * Math.pow((x - xi) / bandwidth, 2)) / (bandwidth * Math.sqrt(2 * Math.PI));

  const yValues = xValues.map((x) => {
    if (margins.length === 0) return 0;
    return margins.reduce((sum, xi) => sum + gaussian(x, xi), 0) / margins.length;
  });

  const maxY = Math.max(...yValues, 0.001);

  const width = 300;
  const height = 80;
  const padding = { top: 8, right: 8, bottom: 20, left: 8 };
  const graphWidth = width - padding.left - padding.right;
  const graphHeight = height - padding.top - padding.bottom;

  const scaleX = (x: number) => padding.left + ((x - xMin) / (xMax - xMin)) * graphWidth;
  const scaleY = (y: number) => padding.top + graphHeight - (y / maxY) * graphHeight;

  const pathData = yValues
    .map((y, i) => `${i === 0 ? "M" : "L"} ${scaleX(xValues[i])} ${scaleY(y)}`)
    .join(" ");

  const fillPath = pathData + ` L ${scaleX(xMax)} ${scaleY(0)} L ${scaleX(xMin)} ${scaleY(0)} Z`;

  return (
    <div className="relative">
      <svg width={width} height={height}>
        <defs>
          <linearGradient id="goldGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#D4AF37" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#D4AF37" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Fill */}
        <path d={fillPath} fill="url(#goldGradient)" />

        {/* Line */}
        <path
          d={pathData}
          fill="none"
          stroke="#D4AF37"
          strokeWidth={1.5}
          strokeLinecap="round"
        />

        {/* Mean marker */}
        <circle
          cx={scaleX(mean)}
          cy={scaleY(yValues[Math.round(((mean - xMin) / (xMax - xMin)) * (points - 1))] || 0)}
          r={3}
          fill="#D4AF37"
        />

        {/* X-axis */}
        <line
          x1={padding.left}
          y1={padding.top + graphHeight}
          x2={width - padding.right}
          y2={padding.top + graphHeight}
          stroke="#3d3d3d"
          strokeWidth={1}
        />

        {[-20, 0, 20].map((tick) => (
          <text
            key={tick}
            x={scaleX(tick)}
            y={height - 4}
            textAnchor="middle"
            fill="#6b6b6b"
            fontSize="9"
            fontFamily="'Cormorant Garamond', serif"
          >
            {tick > 0 ? "+" : ""}{tick}
          </text>
        ))}
      </svg>
    </div>
  );
}

// Luxury team card
function LuxuryTeamCard({ team, isHome }: { team: typeof MOCK_GAME.homeTeam; isHome: boolean }) {
  return (
    <div
      className="relative rounded-2xl overflow-hidden"
      style={{
        background: "linear-gradient(145deg, #1a1a1a 0%, #0d0d0d 100%)",
        boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255,255,255,0.05)"
      }}
    >
      {/* Art deco corner accents */}
      <div className="absolute top-0 left-0 w-20 h-20">
        <svg viewBox="0 0 80 80" className="w-full h-full">
          <path d="M0 0 L40 0 L40 4 L4 4 L4 40 L0 40 Z" fill="#D4AF37" opacity="0.3" />
          <path d="M0 0 L20 0 L20 2 L2 2 L2 20 L0 20 Z" fill="#D4AF37" opacity="0.5" />
        </svg>
      </div>
      <div className="absolute top-0 right-0 w-20 h-20 transform rotate-90">
        <svg viewBox="0 0 80 80" className="w-full h-full">
          <path d="M0 0 L40 0 L40 4 L4 4 L4 40 L0 40 Z" fill="#D4AF37" opacity="0.3" />
          <path d="M0 0 L20 0 L20 2 L2 2 L2 20 L0 20 Z" fill="#D4AF37" opacity="0.5" />
        </svg>
      </div>

      {/* Team color accent line */}
      <div
        className="h-1"
        style={{ background: `linear-gradient(90deg, transparent, ${team.primaryColor}, ${team.secondaryColor}, transparent)` }}
      />

      <div className="p-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              {team.rank && (
                <span className="text-xs text-[#D4AF37] font-medium tracking-widest">NO. {team.rank}</span>
              )}
              <span
                className="text-xs px-3 py-1 rounded-full border"
                style={{
                  color: isHome ? "#4ade80" : "#f87171",
                  borderColor: isHome ? "#4ade8040" : "#f8717140"
                }}
              >
                {isHome ? "HOME" : "AWAY"}
              </span>
            </div>
            <h2
              className="text-3xl text-white mb-1"
              style={{ fontFamily: "'Cormorant Garamond', serif", fontWeight: 500 }}
            >
              {team.name}
            </h2>
            <p className="text-[#6b6b6b] text-sm tracking-wide">{team.conference} Conference</p>
          </div>

          {/* Team crest */}
          <div
            className="w-16 h-16 rounded-xl flex items-center justify-center text-2xl font-bold"
            style={{
              background: `linear-gradient(135deg, ${team.primaryColor}30, ${team.primaryColor}10)`,
              border: `1px solid ${team.primaryColor}40`,
              color: team.primaryColor
            }}
          >
            {team.shortName.charAt(0)}
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          {[
            { label: "Overall", value: team.record },
            { label: "Conference", value: team.confRecord },
            { label: "Against Spread", value: team.atsRecord },
            { label: "Over/Under", value: team.ouRecord },
          ].map((stat) => (
            <div key={stat.label} className="border-l-2 border-[#D4AF37]/30 pl-4">
              <div className="text-[10px] text-[#6b6b6b] uppercase tracking-widest mb-1">{stat.label}</div>
              <div
                className="text-xl text-white"
                style={{ fontFamily: "'Cormorant Garamond', serif" }}
              >
                {stat.value}
              </div>
            </div>
          ))}
        </div>

        {/* Form */}
        <div className="mb-8">
          <div className="text-[10px] text-[#6b6b6b] uppercase tracking-widest mb-3">Recent Performance</div>
          <div className="flex gap-2">
            {team.recentForm.map((result, i) => (
              <div
                key={i}
                className="w-10 h-10 rounded-lg flex items-center justify-center text-sm font-medium border"
                style={{
                  background: result === "W" ? "rgba(34, 197, 94, 0.1)" : "rgba(239, 68, 68, 0.1)",
                  borderColor: result === "W" ? "rgba(34, 197, 94, 0.3)" : "rgba(239, 68, 68, 0.3)",
                  color: result === "W" ? "#4ade80" : "#f87171"
                }}
              >
                {result}
              </div>
            ))}
          </div>
        </div>

        {/* Distribution */}
        {team.spreadDistribution && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="text-[10px] text-[#6b6b6b] uppercase tracking-widest">Spread Distribution</div>
              <div className="flex items-center gap-4">
                <span className="text-xs text-[#6b6b6b]">σ = {team.spreadDistribution.std.toFixed(1)}</span>
                <span
                  className="text-sm font-medium px-2 py-0.5 rounded"
                  style={{
                    background: "rgba(212, 175, 55, 0.15)",
                    color: "#D4AF37"
                  }}
                >
                  {team.spreadDistribution.predictability}%
                </span>
              </div>
            </div>
            <LuxuryKDE
              margins={team.spreadDistribution.margins}
              mean={team.spreadDistribution.mean}
              std={team.spreadDistribution.std}
              predictability={team.spreadDistribution.predictability}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default function LuxuryPremiumDesign() {
  const game = MOCK_GAME;

  return (
    <div
      className="min-h-screen"
      style={{
        background: "#0a0a0a",
        fontFamily: "'Inter', -apple-system, sans-serif"
      }}
    >
      {/* Subtle texture overlay */}
      <div
        className="fixed inset-0 pointer-events-none opacity-30"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }}
      />

      {/* Header */}
      <header className="relative border-b border-[#1a1a1a]">
        <div className="max-w-6xl mx-auto px-8 py-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <img
                src="/logo.jpeg"
                alt="Spread Eagle"
                className="w-14 h-14 rounded-xl"
                style={{ boxShadow: "0 0 30px rgba(212, 175, 55, 0.2)" }}
              />
              <div>
                <h1
                  className="text-2xl text-white tracking-wide"
                  style={{ fontFamily: "'Cormorant Garamond', serif", fontWeight: 500 }}
                >
                  Spread Eagle
                </h1>
                <p className="text-[10px] text-[#D4AF37] uppercase tracking-[0.3em]">
                  Premium Analytics
                </p>
              </div>
            </div>

            <div className="text-right">
              <div className="text-[10px] text-[#6b6b6b] uppercase tracking-widest mb-1">Game Day</div>
              <div
                className="text-lg text-white"
                style={{ fontFamily: "'Cormorant Garamond', serif" }}
              >
                February 1, 2025
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="relative max-w-6xl mx-auto px-8 py-12">
        {/* Matchup header */}
        <div className="text-center mb-16">
          <div className="text-[10px] text-[#6b6b6b] uppercase tracking-[0.3em] mb-6">
            {game.gameTime} • {game.venue}
          </div>

          <div className="flex items-center justify-center gap-12">
            <div className="text-right">
              <div className="text-xs text-[#D4AF37] mb-1">#{game.awayTeam.rank}</div>
              <div
                className="text-4xl text-white"
                style={{ fontFamily: "'Cormorant Garamond', serif" }}
              >
                {game.awayTeam.shortName}
              </div>
            </div>

            <div className="text-[#3d3d3d] text-2xl" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
              at
            </div>

            <div className="text-left">
              <div className="text-xs text-[#D4AF37] mb-1">#{game.homeTeam.rank}</div>
              <div
                className="text-4xl text-white"
                style={{ fontFamily: "'Cormorant Garamond', serif" }}
              >
                {game.homeTeam.shortName}
              </div>
            </div>
          </div>
        </div>

        {/* Lines */}
        <div className="flex justify-center gap-8 mb-16">
          {[
            { label: "Spread", value: game.spread },
            { label: "Total", value: game.total },
          ].map((line) => (
            <div
              key={line.label}
              className="text-center px-12 py-6 rounded-xl border"
              style={{
                background: "linear-gradient(145deg, #141414 0%, #0d0d0d 100%)",
                borderColor: "#1a1a1a"
              }}
            >
              <div className="text-[10px] text-[#6b6b6b] uppercase tracking-widest mb-2">{line.label}</div>
              <div
                className="text-3xl text-white"
                style={{ fontFamily: "'Cormorant Garamond', serif" }}
              >
                {line.value}
              </div>
            </div>
          ))}

          <div
            className="text-center px-12 py-6 rounded-xl border"
            style={{
              background: "linear-gradient(145deg, rgba(212, 175, 55, 0.1) 0%, rgba(212, 175, 55, 0.02) 100%)",
              borderColor: "rgba(212, 175, 55, 0.3)"
            }}
          >
            <div className="text-[10px] text-[#D4AF37] uppercase tracking-widest mb-2">Eagle Score</div>
            <div
              className="text-3xl"
              style={{ fontFamily: "'Cormorant Garamond', serif", color: "#D4AF37" }}
            >
              {game.spreadEagleScore}
            </div>
          </div>
        </div>

        {/* Verdict */}
        <div className="text-center mb-16">
          <div
            className="inline-block px-8 py-3 rounded-full border"
            style={{
              borderColor: "#D4AF37",
              color: "#D4AF37"
            }}
          >
            <span
              className="text-sm tracking-[0.2em] uppercase"
              style={{ fontFamily: "'Cormorant Garamond', serif" }}
            >
              {game.spreadEagleVerdict}
            </span>
          </div>
        </div>

        {/* Team cards */}
        <div className="grid lg:grid-cols-2 gap-8">
          <LuxuryTeamCard team={game.awayTeam} isHome={false} />
          <LuxuryTeamCard team={game.homeTeam} isHome={true} />
        </div>
      </main>

      {/* Footer */}
      <footer className="relative border-t border-[#1a1a1a] mt-16">
        <div className="max-w-6xl mx-auto px-8 py-8 text-center">
          <p className="text-[10px] text-[#3d3d3d] uppercase tracking-[0.2em]">
            Spread Eagle • Probability-First Analytics • Not Financial Advice
          </p>
        </div>
      </footer>
    </div>
  );
}
