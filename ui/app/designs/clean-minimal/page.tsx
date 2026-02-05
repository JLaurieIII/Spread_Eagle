"use client";

import React from "react";

/**
 * SPREAD EAGLE - CLEAN MINIMAL EDITION
 *
 * Design Direction: Swiss-inspired minimalism with surgical precision
 * - Crisp white background with strategic use of negative space
 * - Thin lines and geometric precision
 * - Team colors as the only accent, used sparingly but boldly
 * - Typography-focused with a refined serif/sans combo
 * - Data visualizations as art pieces
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

// Minimal KDE visualization
function MinimalKDE({
  margins,
  mean,
  std,
  predictability,
  accentColor,
}: {
  margins: number[];
  mean: number;
  std: number;
  predictability: number;
  accentColor: string;
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

  const width = 320;
  const height = 100;
  const padding = { top: 8, right: 8, bottom: 24, left: 8 };
  const graphWidth = width - padding.left - padding.right;
  const graphHeight = height - padding.top - padding.bottom;

  const scaleX = (x: number) => padding.left + ((x - xMin) / (xMax - xMin)) * graphWidth;
  const scaleY = (y: number) => padding.top + graphHeight - (y / maxY) * graphHeight;

  const pathData = yValues
    .map((y, i) => `${i === 0 ? "M" : "L"} ${scaleX(xValues[i])} ${scaleY(y)}`)
    .join(" ");

  return (
    <div className="relative">
      <svg width={width} height={height}>
        {/* Zero line */}
        <line
          x1={scaleX(0)}
          y1={padding.top}
          x2={scaleX(0)}
          y2={padding.top + graphHeight}
          stroke="#e5e7eb"
          strokeWidth={1}
        />

        {/* KDE line */}
        <path
          d={pathData}
          fill="none"
          stroke={accentColor}
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Mean dot */}
        <circle
          cx={scaleX(mean)}
          cy={scaleY(yValues[Math.round(((mean - xMin) / (xMax - xMin)) * (points - 1))] || 0)}
          r={4}
          fill={accentColor}
        />

        {/* X-axis */}
        <line
          x1={padding.left}
          y1={padding.top + graphHeight}
          x2={width - padding.right}
          y2={padding.top + graphHeight}
          stroke="#e5e7eb"
          strokeWidth={1}
        />

        {/* X labels */}
        {[-20, 0, 20].map((tick) => (
          <text
            key={tick}
            x={scaleX(tick)}
            y={height - 4}
            textAnchor="middle"
            fill="#9ca3af"
            fontSize="10"
            fontFamily="'DM Mono', monospace"
          >
            {tick > 0 ? "+" : ""}{tick}
          </text>
        ))}
      </svg>

      {/* Stats overlay */}
      <div className="absolute top-0 right-0 text-right">
        <div className="text-xs text-gray-400 font-mono">σ {std.toFixed(1)}</div>
        <div
          className="text-lg font-light"
          style={{ color: accentColor }}
        >
          {predictability}%
        </div>
      </div>
    </div>
  );
}

// Minimal team section
function MinimalTeamSection({ team, isHome }: { team: typeof MOCK_GAME.homeTeam; isHome: boolean }) {
  return (
    <div className="py-12 border-b border-gray-100 last:border-b-0">
      {/* Team header */}
      <div className="flex items-baseline justify-between mb-8">
        <div className="flex items-baseline gap-4">
          {team.rank && (
            <span className="text-sm text-gray-400 font-mono">#{team.rank}</span>
          )}
          <h2
            className="text-4xl font-light tracking-tight"
            style={{ fontFamily: "'Cormorant Garamond', serif" }}
          >
            {team.name}
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{team.conference}</span>
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: team.primaryColor }}
          />
        </div>
      </div>

      {/* Stats in a clean horizontal layout */}
      <div className="grid grid-cols-4 gap-8 mb-10">
        {[
          { label: "Record", value: team.record },
          { label: "Conference", value: team.confRecord },
          { label: "vs Spread", value: team.atsRecord },
          { label: "Over/Under", value: team.ouRecord },
        ].map((stat) => (
          <div key={stat.label}>
            <div className="text-xs text-gray-400 uppercase tracking-widest mb-1">{stat.label}</div>
            <div className="text-2xl font-light text-gray-900" style={{ fontFamily: "'DM Mono', monospace" }}>
              {stat.value}
            </div>
          </div>
        ))}
      </div>

      {/* Recent form */}
      <div className="flex items-center gap-6 mb-10">
        <span className="text-xs text-gray-400 uppercase tracking-widest">Form</span>
        <div className="flex gap-2">
          {team.recentForm.map((result, i) => (
            <div
              key={i}
              className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium"
              style={{
                backgroundColor: result === "W" ? "#f0fdf4" : "#fef2f2",
                color: result === "W" ? "#166534" : "#991b1b",
                border: `1px solid ${result === "W" ? "#bbf7d0" : "#fecaca"}`
              }}
            >
              {result}
            </div>
          ))}
        </div>
      </div>

      {/* KDE Graph */}
      {team.spreadDistribution && (
        <div className="pt-6 border-t border-gray-100">
          <div className="text-xs text-gray-400 uppercase tracking-widest mb-4">Spread Distribution</div>
          <MinimalKDE
            margins={team.spreadDistribution.margins}
            mean={team.spreadDistribution.mean}
            std={team.spreadDistribution.std}
            predictability={team.spreadDistribution.predictability}
            accentColor={team.primaryColor}
          />
        </div>
      )}
    </div>
  );
}

export default function CleanMinimalDesign() {
  const game = MOCK_GAME;

  return (
    <div
      className="min-h-screen bg-white"
      style={{ fontFamily: "'Inter', -apple-system, sans-serif" }}
    >
      {/* Header */}
      <header className="border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <img
                src="/logo.jpeg"
                alt="Spread Eagle"
                className="w-10 h-10 rounded-lg"
              />
              <div>
                <h1 className="text-lg font-semibold text-gray-900 tracking-tight">Spread Eagle</h1>
                <p className="text-xs text-gray-400 tracking-wide">Probability Analytics</p>
              </div>
            </div>
            <div className="text-sm text-gray-500 font-mono">
              {game.gameDate}
            </div>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-4xl mx-auto px-8 py-16">
        {/* Game title */}
        <div className="text-center mb-16">
          <p className="text-sm text-gray-400 tracking-widest uppercase mb-4">
            {game.gameTime} • {game.venue}
          </p>

          <div className="flex items-center justify-center gap-6">
            <span
              className="text-2xl font-light"
              style={{ color: game.awayTeam.primaryColor, fontFamily: "'Cormorant Garamond', serif" }}
            >
              {game.awayTeam.shortName}
            </span>
            <span className="text-gray-300 text-xl">at</span>
            <span
              className="text-2xl font-light"
              style={{ color: game.homeTeam.primaryColor, fontFamily: "'Cormorant Garamond', serif" }}
            >
              {game.homeTeam.shortName}
            </span>
          </div>
        </div>

        {/* Lines - clean horizontal */}
        <div className="flex justify-center gap-16 mb-16 pb-16 border-b border-gray-100">
          <div className="text-center">
            <div className="text-xs text-gray-400 uppercase tracking-widest mb-2">Spread</div>
            <div className="text-3xl font-light text-gray-900 font-mono">{game.spread}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-400 uppercase tracking-widest mb-2">Total</div>
            <div className="text-3xl font-light text-gray-900 font-mono">{game.total}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-400 uppercase tracking-widest mb-2">Eagle Score</div>
            <div className="text-3xl font-light font-mono" style={{ color: "#B8860B" }}>{game.spreadEagleScore}</div>
          </div>
        </div>

        {/* Team sections */}
        <MinimalTeamSection team={game.awayTeam} isHome={false} />
        <MinimalTeamSection team={game.homeTeam} isHome={true} />

        {/* Verdict */}
        <div className="text-center py-16 border-t border-gray-100 mt-8">
          <div className="text-xs text-gray-400 uppercase tracking-widest mb-3">Analysis</div>
          <div
            className="inline-block px-6 py-3 text-sm font-medium tracking-widest uppercase"
            style={{
              color: "#B8860B",
              border: "1px solid #B8860B",
            }}
          >
            {game.spreadEagleVerdict}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-100">
        <div className="max-w-4xl mx-auto px-8 py-6">
          <p className="text-xs text-gray-400 text-center tracking-wide">
            Spread Eagle • Probability-First Analytics • Not Financial Advice
          </p>
        </div>
      </footer>
    </div>
  );
}
