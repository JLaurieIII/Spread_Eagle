"use client";

import React, { useState } from "react";

/**
 * SPREAD EAGLE - PATRIOT DARK EDITION
 *
 * Design Direction: Bold American patriotism meets premium dark mode sports betting
 * - Deep navy (#0a1628) base with metallic gold accents
 * - Red, white, and blue accents pulled from the logo
 * - Military-inspired typography with sharp angles
 * - Dramatic shadows and glowing effects
 * - Team colors as vibrant focal points against dark canvas
 */

// Mock data matching the real API structure
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
    totalDistribution: {
      margins: [3, -5, 8, -2, 4, 7, -6, 2, 5, -3, 1, 6, -4, 3, 2],
      mean: 1.4,
      std: 4.8,
      predictability: 72,
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
    totalDistribution: {
      margins: [-4, 6, -2, 3, -7, 5, 2, -3, 4, 1, -5, 3, 6, -2, 4],
      mean: 0.8,
      std: 4.2,
      predictability: 74,
    },
  },
  spreadPredictability: 66,
  totalPredictability: 73,
  spreadEagleScore: 71,
  spreadEagleVerdict: "STRONG PLAY",
};

// KDE Graph component with patriotic styling
function PatriotKDEGraph({
  margins,
  mean,
  std,
  predictability,
  teamColor,
  label,
}: {
  margins: number[];
  mean: number;
  std: number;
  predictability: number;
  teamColor: string;
  label: string;
}) {
  const bandwidth = std * 0.5 || 5;
  const xMin = -30;
  const xMax = 30;
  const points = 60;
  const xValues = Array.from({ length: points }, (_, i) => xMin + (i * (xMax - xMin)) / (points - 1));

  const gaussian = (x: number, xi: number) =>
    Math.exp(-0.5 * Math.pow((x - xi) / bandwidth, 2)) / (bandwidth * Math.sqrt(2 * Math.PI));

  const yValues = xValues.map((x) => {
    if (margins.length === 0) return 0;
    return margins.reduce((sum, xi) => sum + gaussian(x, xi), 0) / margins.length;
  });

  const maxY = Math.max(...yValues, 0.001);

  const width = 380;
  const height = 140;
  const padding = { top: 16, right: 16, bottom: 32, left: 16 };
  const graphWidth = width - padding.left - padding.right;
  const graphHeight = height - padding.top - padding.bottom;

  const scaleX = (x: number) => padding.left + ((x - xMin) / (xMax - xMin)) * graphWidth;
  const scaleY = (y: number) => padding.top + graphHeight - (y / maxY) * graphHeight;

  const pathData = yValues
    .map((y, i) => `${i === 0 ? "M" : "L"} ${scaleX(xValues[i])} ${scaleY(y)}`)
    .join(" ");

  const fillPath = pathData + ` L ${scaleX(xMax)} ${scaleY(0)} L ${scaleX(xMin)} ${scaleY(0)} Z`;

  const predColor = predictability >= 65 ? "#C9A227" : predictability >= 50 ? "#718096" : "#E53E3E";

  return (
    <div className="relative">
      {/* Glow effect behind graph */}
      <div
        className="absolute inset-0 rounded-xl blur-xl opacity-30"
        style={{ backgroundColor: teamColor }}
      />

      <div
        className="relative rounded-xl p-4 border"
        style={{
          background: "linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 100%)",
          borderColor: teamColor + "40",
          boxShadow: `0 0 30px ${teamColor}20, inset 0 1px 0 rgba(255,255,255,0.05)`
        }}
      >
        <div className="flex items-center justify-between mb-3">
          <span
            className="text-sm font-bold uppercase tracking-widest"
            style={{
              color: teamColor,
              textShadow: `0 0 20px ${teamColor}60`
            }}
          >
            {label}
          </span>
          <div className="flex items-center gap-4">
            <span className="text-xs text-slate-400 font-mono">σ = {std.toFixed(1)}</span>
            <div
              className="px-3 py-1 rounded-md font-bold text-sm"
              style={{
                background: `linear-gradient(135deg, ${predColor}30, ${predColor}10)`,
                color: predColor,
                border: `1px solid ${predColor}50`,
                boxShadow: `0 0 15px ${predColor}30`
              }}
            >
              {predictability.toFixed(0)}%
            </div>
          </div>
        </div>

        <svg width={width} height={height} className="overflow-visible">
          {/* Grid lines */}
          {[-20, -10, 0, 10, 20].map((tick) => (
            <line
              key={tick}
              x1={scaleX(tick)}
              y1={padding.top}
              x2={scaleX(tick)}
              y2={padding.top + graphHeight}
              stroke="#334155"
              strokeWidth={tick === 0 ? 1.5 : 0.5}
              strokeDasharray={tick === 0 ? "none" : "4,4"}
            />
          ))}

          {/* Safe zone glow */}
          <defs>
            <linearGradient id={`safeZone-${label}`} x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#C9A227" stopOpacity="0.15" />
              <stop offset="100%" stopColor="#C9A227" stopOpacity="0" />
            </linearGradient>
          </defs>
          <rect
            x={scaleX(-10)}
            y={padding.top}
            width={scaleX(10) - scaleX(-10)}
            height={graphHeight}
            fill={`url(#safeZone-${label})`}
          />

          {/* KDE fill with gradient */}
          <defs>
            <linearGradient id={`kdeGrad-${label}`} x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={teamColor} stopOpacity="0.4" />
              <stop offset="100%" stopColor={teamColor} stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d={fillPath} fill={`url(#kdeGrad-${label})`} />

          {/* KDE line with glow */}
          <path d={pathData} fill="none" stroke={teamColor} strokeWidth={3} filter="url(#glow)" />
          <defs>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          <path d={pathData} fill="none" stroke={teamColor} strokeWidth={2} />

          {/* Mean marker */}
          <circle
            cx={scaleX(mean)}
            cy={scaleY(yValues[Math.round(((mean - xMin) / (xMax - xMin)) * (points - 1))] || 0)}
            r={6}
            fill={teamColor}
            filter="url(#glow)"
          />
          <circle
            cx={scaleX(mean)}
            cy={scaleY(yValues[Math.round(((mean - xMin) / (xMax - xMin)) * (points - 1))] || 0)}
            r={3}
            fill="#ffffff"
          />

          {/* X-axis */}
          <line
            x1={padding.left}
            y1={padding.top + graphHeight}
            x2={padding.left + graphWidth}
            y2={padding.top + graphHeight}
            stroke="#475569"
            strokeWidth={1}
          />

          {/* X-axis labels */}
          {[-20, -10, 0, 10, 20].map((tick) => (
            <text
              key={tick}
              x={scaleX(tick)}
              y={height - 6}
              textAnchor="middle"
              fill="#94a3b8"
              fontSize="11"
              fontWeight="600"
              fontFamily="'JetBrains Mono', monospace"
            >
              {tick > 0 ? "+" : ""}{tick}
            </text>
          ))}
        </svg>
      </div>
    </div>
  );
}

// Team card with dramatic styling
function PatriotTeamCard({ team, isHome }: { team: typeof MOCK_GAME.homeTeam; isHome: boolean }) {
  return (
    <div className="relative group">
      {/* Outer glow */}
      <div
        className="absolute -inset-1 rounded-2xl blur-lg opacity-40 group-hover:opacity-60 transition-opacity"
        style={{ background: `linear-gradient(135deg, ${team.primaryColor}, ${team.secondaryColor})` }}
      />

      <div
        className="relative rounded-2xl overflow-hidden"
        style={{
          background: `linear-gradient(145deg, ${team.primaryColor}15 0%, #0a1628 50%, ${team.secondaryColor}10 100%)`,
          border: `2px solid ${team.primaryColor}60`
        }}
      >
        {/* Header stripe */}
        <div
          className="h-1.5"
          style={{ background: `linear-gradient(90deg, ${team.primaryColor}, ${team.secondaryColor})` }}
        />

        <div className="p-5">
          {/* Team header */}
          <div className="flex items-center gap-4 mb-5">
            <div
              className="w-16 h-16 rounded-xl flex items-center justify-center text-3xl font-black shadow-2xl"
              style={{
                background: `linear-gradient(135deg, ${team.primaryColor}, ${team.secondaryColor})`,
                boxShadow: `0 10px 40px ${team.primaryColor}50`
              }}
            >
              <span style={{ color: "#ffffff", textShadow: "0 2px 4px rgba(0,0,0,0.3)" }}>
                {team.shortName.charAt(0)}
              </span>
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                {team.rank && (
                  <span
                    className="text-xs font-bold px-2 py-0.5 rounded"
                    style={{
                      background: "#C9A22720",
                      color: "#C9A227",
                      border: "1px solid #C9A22740"
                    }}
                  >
                    #{team.rank}
                  </span>
                )}
                <span
                  className="px-2 py-0.5 rounded text-xs font-semibold"
                  style={{
                    background: isHome ? "#22543D20" : "#74285720",
                    color: isHome ? "#68D391" : "#FC8181",
                    border: `1px solid ${isHome ? "#68D39140" : "#FC818140"}`
                  }}
                >
                  {isHome ? "HOME" : "AWAY"}
                </span>
              </div>
              <h3
                className="text-2xl font-black mt-1 tracking-tight"
                style={{
                  color: "#f8fafc",
                  textShadow: `0 0 30px ${team.primaryColor}40`
                }}
              >
                {team.name}
              </h3>
              <p className="text-slate-500 text-sm font-medium">{team.conference}</p>
            </div>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-4 gap-2 mb-5">
            {[
              { label: "Record", value: team.record },
              { label: "Conf", value: team.confRecord },
              { label: "ATS", value: team.atsRecord },
              { label: "O/U", value: team.ouRecord },
            ].map((stat) => (
              <div
                key={stat.label}
                className="text-center py-3 rounded-lg"
                style={{
                  background: "rgba(30, 41, 59, 0.6)",
                  border: "1px solid rgba(71, 85, 105, 0.3)"
                }}
              >
                <div className="text-lg font-black text-white">{stat.value}</div>
                <div className="text-xs text-slate-500 font-semibold uppercase tracking-wide">{stat.label}</div>
              </div>
            ))}
          </div>

          {/* Recent form */}
          <div className="mb-5">
            <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-2">Recent Form</div>
            <div className="flex gap-1.5">
              {team.recentForm.map((result, i) => (
                <div
                  key={i}
                  className="w-9 h-9 rounded-lg flex items-center justify-center font-bold text-sm"
                  style={{
                    background: result === "W"
                      ? "linear-gradient(135deg, #22543D 0%, #276749 100%)"
                      : "linear-gradient(135deg, #742A2A 0%, #9B2C2C 100%)",
                    boxShadow: result === "W"
                      ? "0 4px 15px rgba(72, 187, 120, 0.3)"
                      : "0 4px 15px rgba(245, 101, 101, 0.3)"
                  }}
                >
                  <span className="text-white">{result}</span>
                </div>
              ))}
            </div>
          </div>

          {/* KDE Graphs */}
          {team.spreadDistribution && (
            <div className="space-y-4">
              <PatriotKDEGraph
                margins={team.spreadDistribution.margins}
                mean={team.spreadDistribution.mean}
                std={team.spreadDistribution.std}
                predictability={team.spreadDistribution.predictability}
                teamColor={team.primaryColor}
                label="Spread Distribution"
              />
              {team.totalDistribution && (
                <PatriotKDEGraph
                  margins={team.totalDistribution.margins}
                  mean={team.totalDistribution.mean}
                  std={team.totalDistribution.std}
                  predictability={team.totalDistribution.predictability}
                  teamColor={team.secondaryColor}
                  label="Total Distribution"
                />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function PatriotDarkDesign() {
  const game = MOCK_GAME;

  return (
    <div
      className="min-h-screen"
      style={{
        background: "linear-gradient(180deg, #0a1628 0%, #0f172a 50%, #0a1628 100%)",
        fontFamily: "'Inter', -apple-system, sans-serif"
      }}
    >
      {/* Patriotic accent lines at top */}
      <div className="h-1 flex">
        <div className="flex-1" style={{ background: "#B91C1C" }} />
        <div className="flex-1" style={{ background: "#ffffff" }} />
        <div className="flex-1" style={{ background: "#1E40AF" }} />
      </div>

      {/* Header */}
      <header className="relative border-b border-slate-800/50">
        <div
          className="absolute inset-0"
          style={{
            background: "radial-gradient(ellipse at top, rgba(201, 162, 39, 0.1) 0%, transparent 50%)"
          }}
        />
        <div className="relative max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <img
                src="/logo.jpeg"
                alt="Spread Eagle"
                className="w-16 h-16 rounded-xl shadow-2xl"
                style={{ boxShadow: "0 0 40px rgba(201, 162, 39, 0.3)" }}
              />
              <div>
                <h1
                  className="text-3xl font-black tracking-tight"
                  style={{
                    background: "linear-gradient(135deg, #C9A227 0%, #FFD700 50%, #C9A227 100%)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    textShadow: "0 0 40px rgba(201, 162, 39, 0.5)"
                  }}
                >
                  SPREAD EAGLE
                </h1>
                <p className="text-slate-500 text-sm font-medium tracking-widest uppercase">
                  Probability-First Analytics
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div
                className="px-4 py-2 rounded-lg font-semibold text-sm"
                style={{
                  background: "rgba(201, 162, 39, 0.15)",
                  color: "#C9A227",
                  border: "1px solid rgba(201, 162, 39, 0.3)"
                }}
              >
                Feb 1, 2025
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Game header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-3 mb-4">
            <span className="text-slate-500 font-medium">{game.gameTime}</span>
            <span className="w-1.5 h-1.5 rounded-full bg-slate-600" />
            <span className="text-slate-500 font-medium">{game.venue}</span>
          </div>

          <div className="flex items-center justify-center gap-8">
            <div className="text-right">
              <div className="text-sm text-slate-500 font-semibold mb-1">#{game.awayTeam.rank}</div>
              <div
                className="text-3xl font-black"
                style={{ color: game.awayTeam.primaryColor }}
              >
                {game.awayTeam.shortName}
              </div>
            </div>

            <div className="text-center px-6">
              <div className="text-5xl font-black text-white tracking-tighter">@</div>
            </div>

            <div className="text-left">
              <div className="text-sm text-slate-500 font-semibold mb-1">#{game.homeTeam.rank}</div>
              <div
                className="text-3xl font-black"
                style={{ color: game.homeTeam.primaryColor }}
              >
                {game.homeTeam.shortName}
              </div>
            </div>
          </div>

          {/* Lines */}
          <div className="flex justify-center gap-6 mt-6">
            <div
              className="px-6 py-3 rounded-xl"
              style={{
                background: "rgba(30, 41, 59, 0.8)",
                border: "1px solid rgba(71, 85, 105, 0.3)"
              }}
            >
              <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-1">Spread</div>
              <div className="text-2xl font-black text-white">{game.spread}</div>
            </div>
            <div
              className="px-6 py-3 rounded-xl"
              style={{
                background: "rgba(30, 41, 59, 0.8)",
                border: "1px solid rgba(71, 85, 105, 0.3)"
              }}
            >
              <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-1">Total</div>
              <div className="text-2xl font-black text-white">{game.total}</div>
            </div>
            <div
              className="px-6 py-3 rounded-xl"
              style={{
                background: "linear-gradient(135deg, rgba(201, 162, 39, 0.2) 0%, rgba(201, 162, 39, 0.05) 100%)",
                border: "1px solid rgba(201, 162, 39, 0.3)"
              }}
            >
              <div className="text-xs font-semibold uppercase tracking-wider mb-1" style={{ color: "#C9A227" }}>Eagle Score</div>
              <div className="text-2xl font-black" style={{ color: "#C9A227" }}>{game.spreadEagleScore}</div>
            </div>
          </div>

          {/* Verdict badge */}
          <div className="mt-6">
            <span
              className="inline-block px-6 py-2 rounded-full text-sm font-bold uppercase tracking-widest"
              style={{
                background: "linear-gradient(135deg, #C9A227 0%, #B8860B 100%)",
                color: "#0a1628",
                boxShadow: "0 10px 40px rgba(201, 162, 39, 0.4)"
              }}
            >
              {game.spreadEagleVerdict}
            </span>
          </div>
        </div>

        {/* Team cards */}
        <div className="grid lg:grid-cols-2 gap-8">
          <PatriotTeamCard team={game.awayTeam} isHome={false} />
          <PatriotTeamCard team={game.homeTeam} isHome={true} />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/50 mt-16">
        <div className="max-w-7xl mx-auto px-6 py-6 text-center">
          <p className="text-slate-600 text-sm">
            SPREAD EAGLE • Probability-First Sports Analytics • Not Financial Advice
          </p>
        </div>
      </footer>

      {/* Patriotic accent lines at bottom */}
      <div className="h-1 flex">
        <div className="flex-1" style={{ background: "#1E40AF" }} />
        <div className="flex-1" style={{ background: "#ffffff" }} />
        <div className="flex-1" style={{ background: "#B91C1C" }} />
      </div>
    </div>
  );
}
