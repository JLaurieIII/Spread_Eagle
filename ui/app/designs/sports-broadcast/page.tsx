"use client";

import React, { useState, useEffect } from "react";

/**
 * SPREAD EAGLE - SPORTS BROADCAST EDITION
 *
 * Design Direction: ESPN/Fox Sports broadcast graphics energy
 * - Bold diagonal cuts and angular shapes
 * - High contrast with team colors POPPING
 * - Scoreboard-style layouts
 * - Animated elements and transitions
 * - Glass morphism with vibrant gradients
 * - Breaking news / live ticker energy
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
    shortName: "KU",
    fullName: "Kansas",
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
    shortName: "BU",
    fullName: "Baylor",
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

// Animated bar graph
function BroadcastBarGraph({
  margins,
  teamColor,
  label,
}: {
  margins: number[];
  teamColor: string;
  label: string;
}) {
  const [animated, setAnimated] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setAnimated(true), 100);
    return () => clearTimeout(timer);
  }, []);

  // Create histogram buckets
  const buckets = Array(7).fill(0);
  const bucketLabels = ["< -15", "-15 to -5", "-5 to 0", "0 to 5", "5 to 15", "> 15"];

  margins.forEach((m) => {
    if (m < -15) buckets[0]++;
    else if (m < -5) buckets[1]++;
    else if (m < 0) buckets[2]++;
    else if (m < 5) buckets[3]++;
    else if (m < 15) buckets[4]++;
    else buckets[5]++;
  });

  const maxCount = Math.max(...buckets, 1);

  return (
    <div className="p-4 rounded-lg" style={{ background: "rgba(0,0,0,0.4)" }}>
      <div className="text-xs font-bold uppercase tracking-wider text-white/60 mb-3">{label}</div>
      <div className="flex items-end gap-1 h-20">
        {buckets.slice(0, 6).map((count, i) => (
          <div key={i} className="flex-1 flex flex-col items-center gap-1">
            <div
              className="w-full rounded-t transition-all duration-700 ease-out"
              style={{
                height: animated ? `${(count / maxCount) * 100}%` : "0%",
                background: `linear-gradient(180deg, ${teamColor} 0%, ${teamColor}80 100%)`,
                boxShadow: `0 0 10px ${teamColor}60`,
                minHeight: count > 0 ? "4px" : "0px"
              }}
            />
          </div>
        ))}
      </div>
      <div className="flex gap-1 mt-1">
        {bucketLabels.map((label, i) => (
          <div key={i} className="flex-1 text-center text-[8px] text-white/40 font-mono">
            {i === 2 ? "PUSH" : i < 2 ? "MISS" : "COVER"}
          </div>
        ))}
      </div>
    </div>
  );
}

// Team panel with broadcast styling
function BroadcastTeamPanel({ team, isHome }: { team: typeof MOCK_GAME.homeTeam; isHome: boolean }) {
  return (
    <div className="relative overflow-hidden">
      {/* Diagonal background */}
      <div
        className="absolute inset-0"
        style={{
          background: `linear-gradient(135deg, ${team.primaryColor} 0%, ${team.primaryColor}dd 60%, ${team.secondaryColor} 100%)`,
          clipPath: isHome
            ? "polygon(0 0, 100% 0, 100% 100%, 5% 100%)"
            : "polygon(0 0, 95% 0, 100% 100%, 0 100%)"
        }}
      />

      {/* Glass overlay */}
      <div
        className="absolute inset-0"
        style={{
          background: "linear-gradient(180deg, rgba(255,255,255,0.1) 0%, transparent 50%, rgba(0,0,0,0.2) 100%)"
        }}
      />

      <div className="relative p-6">
        {/* Team header */}
        <div className={`flex items-center gap-4 mb-4 ${isHome ? "" : "flex-row-reverse"}`}>
          {/* Logo/Initial */}
          <div
            className="w-20 h-20 rounded-lg flex items-center justify-center text-4xl font-black shadow-2xl transform -skew-x-6"
            style={{
              background: "rgba(255,255,255,0.95)",
              color: team.primaryColor,
            }}
          >
            {team.shortName}
          </div>
          <div className={isHome ? "" : "text-right"}>
            {team.rank && (
              <div className="text-white/80 text-sm font-bold">#{team.rank} RANKED</div>
            )}
            <div className="text-white text-3xl font-black uppercase tracking-tight" style={{ textShadow: "2px 2px 4px rgba(0,0,0,0.3)" }}>
              {team.fullName}
            </div>
            <div className="text-white/70 text-sm font-semibold">{team.conference} Conference</div>
          </div>
        </div>

        {/* Stats bar */}
        <div
          className="flex justify-between items-center p-3 rounded transform -skew-x-3 mb-4"
          style={{ background: "rgba(0,0,0,0.4)" }}
        >
          {[
            { label: "RECORD", value: team.record },
            { label: "CONF", value: team.confRecord },
            { label: "ATS", value: team.atsRecord },
            { label: "O/U", value: team.ouRecord },
          ].map((stat, i) => (
            <div key={stat.label} className={`text-center transform skew-x-3 ${i < 3 ? "border-r border-white/20 pr-4" : ""}`}>
              <div className="text-white/60 text-[10px] font-bold tracking-wider">{stat.label}</div>
              <div className="text-white text-xl font-black">{stat.value}</div>
            </div>
          ))}
        </div>

        {/* Recent form with animation */}
        <div className="flex items-center gap-2 mb-4">
          <span className="text-white/60 text-xs font-bold uppercase">Last 5:</span>
          <div className="flex gap-1">
            {team.recentForm.map((result, i) => (
              <div
                key={i}
                className="w-8 h-8 flex items-center justify-center font-black text-sm transform -skew-x-6 transition-all hover:scale-110"
                style={{
                  background: result === "W" ? "#22c55e" : "#ef4444",
                  boxShadow: `0 4px 15px ${result === "W" ? "rgba(34, 197, 94, 0.5)" : "rgba(239, 68, 68, 0.5)"}`
                }}
              >
                <span className="transform skew-x-6 text-white">{result}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Bar graph */}
        {team.spreadDistribution && (
          <BroadcastBarGraph
            margins={team.spreadDistribution.margins}
            teamColor={team.secondaryColor}
            label="Cover Distribution"
          />
        )}
      </div>
    </div>
  );
}

export default function SportsBroadcastDesign() {
  const game = MOCK_GAME;
  const [showScore, setShowScore] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowScore(true), 500);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div
      className="min-h-screen"
      style={{
        background: "linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 50%, #0f0f0f 100%)",
        fontFamily: "'Oswald', 'Impact', sans-serif"
      }}
    >
      {/* Top ticker bar */}
      <div className="bg-red-600 py-2 overflow-hidden">
        <div className="animate-marquee whitespace-nowrap">
          <span className="text-white font-bold text-sm tracking-wide mx-8">
            🏀 SPREAD EAGLE ANALYTICS • PROBABILITY-FIRST BETTING INTELLIGENCE • COLLEGE BASKETBALL • {game.gameDate}
          </span>
          <span className="text-white font-bold text-sm tracking-wide mx-8">
            🏀 SPREAD EAGLE ANALYTICS • PROBABILITY-FIRST BETTING INTELLIGENCE • COLLEGE BASKETBALL • {game.gameDate}
          </span>
        </div>
      </div>

      {/* Header */}
      <header className="relative">
        <div
          className="absolute inset-0"
          style={{
            background: "linear-gradient(90deg, #B91C1C 0%, #1E3A8A 50%, #B91C1C 100%)",
            clipPath: "polygon(0 0, 100% 0, 100% 80%, 50% 100%, 0 80%)"
          }}
        />
        <div className="relative max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <img
                src="/logo.jpeg"
                alt="Spread Eagle"
                className="w-16 h-16 rounded-lg shadow-2xl transform -rotate-3"
              />
              <div>
                <h1
                  className="text-4xl font-black text-white uppercase tracking-tighter"
                  style={{ textShadow: "3px 3px 6px rgba(0,0,0,0.5)" }}
                >
                  SPREAD EAGLE
                </h1>
                <div className="text-white/80 text-sm font-semibold tracking-widest uppercase">
                  Game Analysis Center
                </div>
              </div>
            </div>
            <div
              className="px-6 py-3 transform -skew-x-6"
              style={{ background: "rgba(0,0,0,0.5)" }}
            >
              <span className="transform skew-x-6 inline-block text-white font-bold text-lg">
                {game.gameTime}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main scoreboard section */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Matchup scoreboard */}
        <div
          className="relative rounded-2xl overflow-hidden mb-8"
          style={{
            background: "linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(50,50,50,0.9) 100%)",
            border: "3px solid rgba(255,255,255,0.1)"
          }}
        >
          {/* Top accent bar */}
          <div className="h-2 flex">
            <div className="flex-1" style={{ background: game.awayTeam.primaryColor }} />
            <div className="flex-1" style={{ background: game.homeTeam.primaryColor }} />
          </div>

          <div className="p-8">
            {/* Matchup header */}
            <div className="flex items-center justify-between mb-8">
              {/* Away team */}
              <div className="flex items-center gap-6">
                <div
                  className="w-24 h-24 rounded-xl flex items-center justify-center text-4xl font-black transform -skew-x-6 shadow-2xl"
                  style={{
                    background: `linear-gradient(135deg, ${game.awayTeam.primaryColor}, ${game.awayTeam.secondaryColor})`,
                  }}
                >
                  <span className="transform skew-x-6 text-white">{game.awayTeam.shortName}</span>
                </div>
                <div>
                  <div className="text-white/60 text-sm font-bold">#{game.awayTeam.rank}</div>
                  <div className="text-white text-4xl font-black uppercase">{game.awayTeam.fullName}</div>
                  <div className="text-white/60 text-lg">{game.awayTeam.record}</div>
                </div>
              </div>

              {/* VS / Lines */}
              <div className="text-center px-8">
                <div className="text-6xl font-black text-white/20 mb-4">VS</div>
                <div className="space-y-2">
                  <div
                    className="px-6 py-2 rounded transform -skew-x-6"
                    style={{ background: "rgba(255,255,255,0.1)" }}
                  >
                    <span className="transform skew-x-6 inline-block">
                      <span className="text-white/60 text-xs font-bold mr-2">SPREAD</span>
                      <span className="text-white text-2xl font-black">{game.spread}</span>
                    </span>
                  </div>
                  <div
                    className="px-6 py-2 rounded transform -skew-x-6"
                    style={{ background: "rgba(255,255,255,0.1)" }}
                  >
                    <span className="transform skew-x-6 inline-block">
                      <span className="text-white/60 text-xs font-bold mr-2">TOTAL</span>
                      <span className="text-white text-2xl font-black">{game.total}</span>
                    </span>
                  </div>
                </div>
              </div>

              {/* Home team */}
              <div className="flex items-center gap-6 flex-row-reverse">
                <div
                  className="w-24 h-24 rounded-xl flex items-center justify-center text-4xl font-black transform -skew-x-6 shadow-2xl"
                  style={{
                    background: `linear-gradient(135deg, ${game.homeTeam.primaryColor}, ${game.homeTeam.secondaryColor})`,
                  }}
                >
                  <span className="transform skew-x-6 text-white">{game.homeTeam.shortName}</span>
                </div>
                <div className="text-right">
                  <div className="text-white/60 text-sm font-bold">#{game.homeTeam.rank}</div>
                  <div className="text-white text-4xl font-black uppercase">{game.homeTeam.fullName}</div>
                  <div className="text-white/60 text-lg">{game.homeTeam.record}</div>
                </div>
              </div>
            </div>

            {/* Eagle Score reveal */}
            <div className="text-center">
              <div
                className={`inline-block transform transition-all duration-700 ${showScore ? "scale-100 opacity-100" : "scale-50 opacity-0"}`}
              >
                <div
                  className="px-12 py-6 rounded-xl transform -skew-x-6"
                  style={{
                    background: "linear-gradient(135deg, #B8860B, #FFD700, #B8860B)",
                    boxShadow: "0 10px 50px rgba(184, 134, 11, 0.5)"
                  }}
                >
                  <div className="transform skew-x-6">
                    <div className="text-black/60 text-sm font-bold tracking-widest mb-1">SPREAD EAGLE SCORE</div>
                    <div className="text-black text-6xl font-black">{game.spreadEagleScore}</div>
                    <div
                      className="mt-2 px-4 py-1 rounded bg-black/20 inline-block text-sm font-bold tracking-wider"
                      style={{ color: "#1a1a1a" }}
                    >
                      {game.spreadEagleVerdict}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Team panels */}
        <div className="grid lg:grid-cols-2 gap-4">
          <BroadcastTeamPanel team={game.awayTeam} isHome={false} />
          <BroadcastTeamPanel team={game.homeTeam} isHome={true} />
        </div>
      </main>

      {/* Bottom ticker */}
      <div className="fixed bottom-0 left-0 right-0 bg-black/90 py-3 border-t-4 border-red-600">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-red-500 font-black text-sm animate-pulse">● LIVE</span>
            <span className="text-white font-bold">SPREAD EAGLE ANALYTICS</span>
          </div>
          <div className="text-white/60 text-sm">
            Not financial advice • Gamble responsibly
          </div>
        </div>
      </div>

      {/* CSS for marquee animation */}
      <style jsx>{`
        @keyframes marquee {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .animate-marquee {
          animation: marquee 20s linear infinite;
        }
      `}</style>
    </div>
  );
}
