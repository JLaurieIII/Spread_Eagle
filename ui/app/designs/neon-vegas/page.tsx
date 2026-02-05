"use client";

import React, { useState, useEffect } from "react";

/**
 * SPREAD EAGLE - NEON VEGAS EDITION
 *
 * Design Direction: Las Vegas sportsbook neon energy
 * - Deep purple/black backgrounds
 * - Neon pink, cyan, and electric yellow accents
 * - Glowing text and borders
 * - Retro-futuristic grid patterns
 * - Pulsing animations
 * - Team colors as neon accents
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

// Neon glow text component
function NeonText({
  children,
  color,
  size = "md",
  pulse = false,
}: {
  children: React.ReactNode;
  color: string;
  size?: "sm" | "md" | "lg" | "xl";
  pulse?: boolean;
}) {
  const sizes = {
    sm: "text-sm",
    md: "text-xl",
    lg: "text-3xl",
    xl: "text-5xl",
  };

  return (
    <span
      className={`${sizes[size]} font-black uppercase tracking-wider ${pulse ? "animate-pulse" : ""}`}
      style={{
        color: color,
        textShadow: `
          0 0 5px ${color},
          0 0 10px ${color},
          0 0 20px ${color},
          0 0 40px ${color}80
        `,
      }}
    >
      {children}
    </span>
  );
}

// Neon KDE visualization
function NeonKDE({
  margins,
  mean,
  std,
  predictability,
  neonColor,
}: {
  margins: number[];
  mean: number;
  std: number;
  predictability: number;
  neonColor: string;
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
    <div className="relative p-4 rounded-lg" style={{ background: "rgba(0,0,0,0.5)" }}>
      <svg width={width} height={height}>
        <defs>
          <filter id="neonGlow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {/* Grid lines */}
        {[-20, -10, 0, 10, 20].map((tick) => (
          <line
            key={tick}
            x1={scaleX(tick)}
            y1={padding.top}
            x2={scaleX(tick)}
            y2={padding.top + graphHeight}
            stroke="#ff00ff"
            strokeOpacity="0.1"
            strokeWidth={tick === 0 ? 1 : 0.5}
          />
        ))}

        {/* KDE line with neon glow */}
        <path
          d={pathData}
          fill="none"
          stroke={neonColor}
          strokeWidth={3}
          filter="url(#neonGlow)"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Mean marker */}
        <circle
          cx={scaleX(mean)}
          cy={scaleY(yValues[Math.round(((mean - xMin) / (xMax - xMin)) * (points - 1))] || 0)}
          r={5}
          fill={neonColor}
          filter="url(#neonGlow)"
        />

        {/* X-axis */}
        <line
          x1={padding.left}
          y1={padding.top + graphHeight}
          x2={width - padding.right}
          y2={padding.top + graphHeight}
          stroke="#ff00ff"
          strokeOpacity="0.3"
          strokeWidth={1}
        />

        {[-20, 0, 20].map((tick) => (
          <text
            key={tick}
            x={scaleX(tick)}
            y={height - 4}
            textAnchor="middle"
            fill="#00ffff"
            fontSize="10"
            fontFamily="'Orbitron', monospace"
            style={{ textShadow: "0 0 5px #00ffff" }}
          >
            {tick > 0 ? "+" : ""}{tick}
          </text>
        ))}
      </svg>

      {/* Predictability score */}
      <div className="absolute top-2 right-4 flex items-center gap-2">
        <span className="text-xs text-purple-400">σ {std.toFixed(1)}</span>
        <span
          className="text-lg font-black"
          style={{
            color: "#00ff00",
            textShadow: "0 0 10px #00ff00, 0 0 20px #00ff00"
          }}
        >
          {predictability}%
        </span>
      </div>
    </div>
  );
}

// Neon team card
function NeonTeamCard({ team, isHome }: { team: typeof MOCK_GAME.homeTeam; isHome: boolean }) {
  const neonPrimary = team.primaryColor;
  const neonSecondary = team.secondaryColor;

  return (
    <div
      className="relative rounded-2xl overflow-hidden"
      style={{
        background: "linear-gradient(135deg, #0f0014 0%, #1a0029 50%, #0f0014 100%)",
        boxShadow: `
          0 0 20px ${neonPrimary}40,
          inset 0 0 60px ${neonPrimary}10,
          0 0 100px ${neonPrimary}20
        `,
        border: `2px solid ${neonPrimary}60`
      }}
    >
      {/* Scan line effect */}
      <div
        className="absolute inset-0 pointer-events-none opacity-10"
        style={{
          background: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.03) 2px, rgba(255,255,255,0.03) 4px)"
        }}
      />

      {/* Corner accents */}
      <div
        className="absolute top-0 left-0 w-16 h-16"
        style={{
          borderTop: `3px solid ${neonPrimary}`,
          borderLeft: `3px solid ${neonPrimary}`,
          boxShadow: `inset 5px 5px 20px ${neonPrimary}40`
        }}
      />
      <div
        className="absolute bottom-0 right-0 w-16 h-16"
        style={{
          borderBottom: `3px solid ${neonSecondary}`,
          borderRight: `3px solid ${neonSecondary}`,
          boxShadow: `inset -5px -5px 20px ${neonSecondary}40`
        }}
      />

      <div className="relative p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              {team.rank && (
                <NeonText color="#ff00ff" size="sm">#{team.rank}</NeonText>
              )}
              <span
                className="text-xs px-3 py-1 rounded border font-bold uppercase tracking-wider"
                style={{
                  color: isHome ? "#00ff00" : "#ff0066",
                  borderColor: isHome ? "#00ff0060" : "#ff006660",
                  textShadow: isHome ? "0 0 10px #00ff00" : "0 0 10px #ff0066"
                }}
              >
                {isHome ? "HOME" : "AWAY"}
              </span>
            </div>
            <h2
              className="text-3xl font-black uppercase tracking-wider"
              style={{
                color: neonPrimary,
                textShadow: `0 0 10px ${neonPrimary}, 0 0 30px ${neonPrimary}80`
              }}
            >
              {team.name}
            </h2>
            <p className="text-purple-400 text-sm mt-1" style={{ fontFamily: "'Orbitron', monospace" }}>
              {team.conference}
            </p>
          </div>

          {/* Glowing initial */}
          <div
            className="w-20 h-20 rounded-xl flex items-center justify-center text-4xl font-black"
            style={{
              background: `linear-gradient(135deg, ${neonPrimary}20, ${neonSecondary}20)`,
              border: `2px solid ${neonPrimary}`,
              boxShadow: `0 0 30px ${neonPrimary}60, inset 0 0 30px ${neonPrimary}20`,
              color: neonPrimary,
              textShadow: `0 0 20px ${neonPrimary}`
            }}
          >
            {team.shortName.charAt(0)}
          </div>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-4 gap-3 mb-6">
          {[
            { label: "REC", value: team.record },
            { label: "CONF", value: team.confRecord },
            { label: "ATS", value: team.atsRecord },
            { label: "O/U", value: team.ouRecord },
          ].map((stat) => (
            <div
              key={stat.label}
              className="text-center p-3 rounded-lg"
              style={{
                background: "rgba(255,0,255,0.05)",
                border: "1px solid rgba(255,0,255,0.2)"
              }}
            >
              <div
                className="text-xl font-black"
                style={{ color: "#00ffff", textShadow: "0 0 10px #00ffff" }}
              >
                {stat.value}
              </div>
              <div
                className="text-[10px] text-purple-400 uppercase tracking-wider"
                style={{ fontFamily: "'Orbitron', monospace" }}
              >
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        {/* Recent form */}
        <div className="mb-6">
          <div
            className="text-xs text-purple-400 uppercase tracking-wider mb-3"
            style={{ fontFamily: "'Orbitron', monospace" }}
          >
            RECENT FORM
          </div>
          <div className="flex gap-2">
            {team.recentForm.map((result, i) => (
              <div
                key={i}
                className="w-10 h-10 rounded-lg flex items-center justify-center font-black text-sm"
                style={{
                  background: result === "W" ? "rgba(0,255,0,0.1)" : "rgba(255,0,102,0.1)",
                  border: `2px solid ${result === "W" ? "#00ff00" : "#ff0066"}`,
                  color: result === "W" ? "#00ff00" : "#ff0066",
                  boxShadow: result === "W" ? "0 0 15px #00ff0060" : "0 0 15px #ff006660",
                  textShadow: result === "W" ? "0 0 10px #00ff00" : "0 0 10px #ff0066"
                }}
              >
                {result}
              </div>
            ))}
          </div>
        </div>

        {/* KDE */}
        {team.spreadDistribution && (
          <div>
            <div
              className="text-xs text-purple-400 uppercase tracking-wider mb-3"
              style={{ fontFamily: "'Orbitron', monospace" }}
            >
              SPREAD DISTRIBUTION
            </div>
            <NeonKDE
              margins={team.spreadDistribution.margins}
              mean={team.spreadDistribution.mean}
              std={team.spreadDistribution.std}
              predictability={team.spreadDistribution.predictability}
              neonColor={neonPrimary}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default function NeonVegasDesign() {
  const game = MOCK_GAME;
  const [glitch, setGlitch] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setGlitch(true);
      setTimeout(() => setGlitch(false), 100);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div
      className="min-h-screen"
      style={{
        background: "linear-gradient(180deg, #0a000f 0%, #1a0029 50%, #0a000f 100%)",
        fontFamily: "'Inter', sans-serif"
      }}
    >
      {/* Retro grid background */}
      <div
        className="fixed inset-0 pointer-events-none opacity-20"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,0,255,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,0,255,0.1) 1px, transparent 1px)
          `,
          backgroundSize: "50px 50px"
        }}
      />

      {/* Header */}
      <header className="relative border-b border-purple-500/30">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <img
                src="/logo.jpeg"
                alt="Spread Eagle"
                className="w-14 h-14 rounded-xl"
                style={{
                  boxShadow: "0 0 30px rgba(255,0,255,0.5), 0 0 60px rgba(0,255,255,0.3)"
                }}
              />
              <div className={glitch ? "animate-pulse" : ""}>
                <h1
                  className="text-3xl font-black uppercase tracking-wider"
                  style={{
                    color: "#ff00ff",
                    textShadow: "0 0 10px #ff00ff, 0 0 30px #ff00ff, 0 0 60px #ff00ff80",
                    fontFamily: "'Orbitron', sans-serif"
                  }}
                >
                  SPREAD EAGLE
                </h1>
                <p
                  className="text-xs uppercase tracking-[0.3em]"
                  style={{
                    color: "#00ffff",
                    textShadow: "0 0 10px #00ffff"
                  }}
                >
                  VEGAS ANALYTICS
                </p>
              </div>
            </div>

            <div
              className="px-4 py-2 rounded border"
              style={{
                borderColor: "#ff006660",
                color: "#ff0066",
                textShadow: "0 0 10px #ff0066",
                fontFamily: "'Orbitron', monospace"
              }}
            >
              {game.gameTime}
            </div>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="relative max-w-7xl mx-auto px-6 py-12">
        {/* Matchup */}
        <div className="text-center mb-12">
          <div
            className="text-sm text-purple-400 mb-6"
            style={{ fontFamily: "'Orbitron', monospace" }}
          >
            {game.venue} • {game.location}
          </div>

          <div className="flex items-center justify-center gap-8">
            <NeonText color={game.awayTeam.primaryColor} size="xl">
              {game.awayTeam.shortName}
            </NeonText>
            <span
              className="text-4xl"
              style={{
                color: "#ff00ff",
                textShadow: "0 0 20px #ff00ff",
                fontFamily: "'Orbitron', sans-serif"
              }}
            >
              VS
            </span>
            <NeonText color={game.homeTeam.primaryColor} size="xl">
              {game.homeTeam.shortName}
            </NeonText>
          </div>
        </div>

        {/* Lines */}
        <div className="flex justify-center gap-6 mb-12">
          {[
            { label: "SPREAD", value: game.spread, color: "#00ffff" },
            { label: "TOTAL", value: game.total, color: "#ff00ff" },
            { label: "EAGLE", value: game.spreadEagleScore.toString(), color: "#00ff00" },
          ].map((line) => (
            <div
              key={line.label}
              className="text-center px-8 py-6 rounded-xl"
              style={{
                background: "rgba(0,0,0,0.5)",
                border: `2px solid ${line.color}60`,
                boxShadow: `0 0 30px ${line.color}30, inset 0 0 30px ${line.color}10`
              }}
            >
              <div
                className="text-[10px] uppercase tracking-widest mb-2"
                style={{
                  color: line.color,
                  textShadow: `0 0 10px ${line.color}`,
                  fontFamily: "'Orbitron', monospace"
                }}
              >
                {line.label}
              </div>
              <div
                className="text-4xl font-black"
                style={{
                  color: line.color,
                  textShadow: `0 0 10px ${line.color}, 0 0 30px ${line.color}80`
                }}
              >
                {line.value}
              </div>
            </div>
          ))}
        </div>

        {/* Verdict */}
        <div className="text-center mb-12">
          <div
            className="inline-block px-8 py-4 rounded-xl animate-pulse"
            style={{
              background: "linear-gradient(135deg, rgba(0,255,0,0.1), rgba(0,255,255,0.1))",
              border: "2px solid #00ff00",
              boxShadow: "0 0 30px #00ff0060, 0 0 60px #00ff0030"
            }}
          >
            <NeonText color="#00ff00" size="lg">
              {game.spreadEagleVerdict}
            </NeonText>
          </div>
        </div>

        {/* Team cards */}
        <div className="grid lg:grid-cols-2 gap-8">
          <NeonTeamCard team={game.awayTeam} isHome={false} />
          <NeonTeamCard team={game.homeTeam} isHome={true} />
        </div>
      </main>

      {/* Footer */}
      <footer className="relative border-t border-purple-500/30 mt-16">
        <div className="max-w-7xl mx-auto px-6 py-6 text-center">
          <p
            className="text-xs text-purple-400 tracking-wide"
            style={{ fontFamily: "'Orbitron', monospace" }}
          >
            SPREAD EAGLE • PROBABILITY-FIRST ANALYTICS • NOT FINANCIAL ADVICE
          </p>
        </div>
      </footer>

      {/* Google Fonts link for Orbitron */}
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
      `}</style>
    </div>
  );
}
