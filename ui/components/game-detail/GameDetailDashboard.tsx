"use client";

import React, { useState, useEffect } from "react";
import "./flag-animations.css";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  ReferenceLine,
} from "recharts";

// ============================================================================
// TYPES
// ============================================================================

interface Team {
  name: string;
  abbreviation: string;
  primaryColor: string;
  secondaryColor: string;
  logo: string;
  record: string;
  ranking?: number;
}

interface CurrentLine {
  spread: number;
  spreadFavorite: string;
  overUnder: number;
  homeMoneyline: number;
  awayMoneyline: number;
}

interface GameData {
  gameId: string;
  gameTime: string;
  venue: string;
  homeTeam: Team;
  awayTeam: Team;
  currentLine: CurrentLine;
}

interface SpreadProbability {
  spread: number;
  probability: number;
  edge: number;
}

interface OverUnderProbability {
  total: number;
  overProb: number;
  underProb: number;
}

interface Sportsbook {
  name: string;
  spread: number;
  spreadOdds: number;
  ou: number;
  ouOdds: number;
  ml: number;
}

interface TeamStats {
  spPlusOverall: number;
  spPlusOffense: number;
  spPlusDefense: number;
  offenseRank: number;
  defenseRank: number;
  ppg: number;
  oppPpg: number;
  yardsPg: number;
  rushYpg: number;
  passYpg: number;
  thirdDownPct: number;
  redZonePct: number;
}

interface EdgeAnalysis {
  spreadEdge: number;
  ouEdge: number;
  mlEdge: number;
  projectedScore: { home: number; away: number };
  projectedTotal: number;
  confidence: number;
}

interface GameDetailDashboardProps {
  gameData?: GameData;
  spreadProbabilityData?: SpreadProbability[];
  overUnderProbabilityData?: OverUnderProbability[];
  sportsbooks?: Sportsbook[];
  teamStats?: { home: TeamStats; away: TeamStats };
  edgeAnalysis?: EdgeAnalysis;
}

// ============================================================================
// SAMPLE DATA - Replace with real API data
// ============================================================================

const defaultGameData: GameData = {
  gameId: "CFB-2024-001",
  gameTime: "2024-11-23T19:30:00Z",
  venue: "Memorial Stadium",
  homeTeam: {
    name: "Nebraska Cornhuskers",
    abbreviation: "NEB",
    primaryColor: "#E41C38",
    secondaryColor: "#F5F5F5",
    logo: "https://a.espncdn.com/i/teamlogos/ncaa/500/158.png",
    record: "8-2",
    ranking: 15,
  },
  awayTeam: {
    name: "Iowa Hawkeyes",
    abbreviation: "IOWA",
    primaryColor: "#FFCD00",
    secondaryColor: "#000000",
    logo: "https://a.espncdn.com/i/teamlogos/ncaa/500/2294.png",
    record: "7-3",
    ranking: 22,
  },
  currentLine: {
    spread: -6.5,
    spreadFavorite: "NEB",
    overUnder: 47.5,
    homeMoneyline: -245,
    awayMoneyline: 205,
  },
};

const defaultSpreadProbabilityData: SpreadProbability[] = [
  { spread: -14, probability: 12, edge: -8 },
  { spread: -10.5, probability: 22, edge: -3 },
  { spread: -7, probability: 38, edge: 2 },
  { spread: -6.5, probability: 42, edge: 4 },
  { spread: -3.5, probability: 55, edge: 8 },
  { spread: -3, probability: 58, edge: 11 },
  { spread: 0, probability: 65, edge: 12 },
  { spread: 3, probability: 72, edge: 9 },
  { spread: 6.5, probability: 82, edge: 6 },
  { spread: 10, probability: 89, edge: 3 },
  { spread: 14, probability: 94, edge: 1 },
];

const defaultOverUnderProbabilityData: OverUnderProbability[] = [
  { total: 38, overProb: 92, underProb: 8 },
  { total: 41, overProb: 84, underProb: 16 },
  { total: 44, overProb: 68, underProb: 32 },
  { total: 47.5, overProb: 52, underProb: 48 },
  { total: 51, overProb: 35, underProb: 65 },
  { total: 54, overProb: 22, underProb: 78 },
  { total: 57, overProb: 12, underProb: 88 },
  { total: 60, overProb: 6, underProb: 94 },
];

const defaultSportsbooks: Sportsbook[] = [
  { name: "DraftKings", spread: -6.5, spreadOdds: -110, ou: 47.5, ouOdds: -110, ml: -245 },
  { name: "FanDuel", spread: -7, spreadOdds: -105, ou: 47, ouOdds: -108, ml: -250 },
  { name: "BetMGM", spread: -6.5, spreadOdds: -108, ou: 48, ouOdds: -112, ml: -240 },
  { name: "Caesars", spread: -6.5, spreadOdds: -112, ou: 47.5, ouOdds: -110, ml: -245 },
  { name: "PointsBet", spread: -7, spreadOdds: -110, ou: 47.5, ouOdds: -105, ml: -255 },
];

const defaultTeamStats = {
  home: {
    spPlusOverall: 18.4,
    spPlusOffense: 32.1,
    spPlusDefense: 14.3,
    offenseRank: 12,
    defenseRank: 8,
    ppg: 34.2,
    oppPpg: 18.7,
    yardsPg: 425.3,
    rushYpg: 198.2,
    passYpg: 227.1,
    thirdDownPct: 44.2,
    redZonePct: 88.5,
  },
  away: {
    spPlusOverall: 12.1,
    spPlusOffense: 18.5,
    spPlusDefense: 24.8,
    offenseRank: 45,
    defenseRank: 5,
    ppg: 24.8,
    oppPpg: 15.2,
    yardsPg: 342.1,
    rushYpg: 156.8,
    passYpg: 185.3,
    thirdDownPct: 38.9,
    redZonePct: 72.4,
  },
};

const defaultEdgeAnalysis: EdgeAnalysis = {
  spreadEdge: 6.2,
  ouEdge: -2.1,
  mlEdge: 4.8,
  projectedScore: { home: 28, away: 20 },
  projectedTotal: 48,
  confidence: 72,
};

// ============================================================================
// UTILITY COMPONENTS
// ============================================================================

const AmericanFlagBackground = () => (
  <div className="absolute inset-0 overflow-hidden pointer-events-none animate-flag-wave">
    {/* Horizontal stripes */}
    <div className="absolute inset-0">
      {[...Array(13)].map((_, i) => (
        <div
          key={`stripe-${i}`}
          className="w-full animate-stripe-wave"
          style={{
            height: "7.69%",
            backgroundColor: i % 2 === 0 ? "rgba(220, 38, 38, 0.15)" : "rgba(255, 255, 255, 0.02)",
            animationDelay: `${i * 0.1}s`,
          }}
        />
      ))}
    </div>

    {/* Star field canton */}
    <div
      className="absolute top-0 left-0 w-[40%] h-[54%] animate-canton-glow"
      style={{ backgroundColor: "rgba(30, 58, 138, 0.25)" }}
    >
      {[...Array(9)].map((_, row) => (
        <div
          key={`star-row-${row}`}
          className="flex justify-around items-center"
          style={{
            height: "11.1%",
            paddingLeft: row % 2 === 1 ? "3%" : "0",
            paddingRight: row % 2 === 1 ? "3%" : "0",
          }}
        >
          {[...Array(row % 2 === 0 ? 6 : 5)].map((_, col) => (
            <span
              key={`star-${row}-${col}`}
              className="text-white text-base animate-star-twinkle"
              style={{ animationDelay: `${(row * 6 + col) * 0.1}s` }}
            >
              ★
            </span>
          ))}
        </div>
      ))}
    </div>

    {/* Scattered stars */}
    {[...Array(35)].map((_, i) => (
      <div
        key={`scatter-${i}`}
        className="absolute text-white animate-star-twinkle"
        style={{
          left: `${45 + Math.random() * 52}%`,
          top: `${Math.random() * 100}%`,
          fontSize: `${12 + Math.random() * 16}px`,
          animationDelay: `${i * 0.15}s`,
          animationDuration: `${2 + Math.random() * 2}s`,
        }}
      >
        ★
      </div>
    ))}

    {/* Gradient overlays */}
    <div
      className="absolute inset-0"
      style={{
        background: `
          radial-gradient(ellipse at 15% 25%, rgba(220, 38, 38, 0.12) 0%, transparent 45%),
          radial-gradient(ellipse at 85% 75%, rgba(30, 64, 175, 0.12) 0%, transparent 45%)
        `,
      }}
    />

    {/* Vignette */}
    <div
      className="absolute inset-0"
      style={{
        background: "radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.3) 100%)",
      }}
    />
  </div>
);

interface EdgeBadgeProps {
  edge: number;
  threshold?: number;
}

const EdgeBadge = ({ edge, threshold = 5 }: EdgeBadgeProps) => {
  const isPositive = edge > 0;
  const isStrong = Math.abs(edge) >= threshold;

  return (
    <div
      className={`
        px-3 py-1 rounded-full text-sm font-bold
        ${isStrong && isPositive ? "bg-green-500 text-white animate-pulse" : ""}
        ${isStrong && !isPositive ? "bg-red-500 text-white" : ""}
        ${!isStrong && isPositive ? "bg-green-500/20 text-green-400 border border-green-500/30" : ""}
        ${!isStrong && !isPositive ? "bg-red-500/20 text-red-400 border border-red-500/30" : ""}
      `}
    >
      {isPositive ? "+" : ""}
      {edge.toFixed(1)}% Edge
    </div>
  );
};

interface DashboardCardProps {
  title: string;
  children: React.ReactNode;
  className?: string;
  highlight?: boolean;
}

const DashboardCard = ({ title, children, className = "", highlight = false }: DashboardCardProps) => (
  <div
    className={`
      relative bg-slate-800/80 backdrop-blur-sm rounded-xl border overflow-hidden
      transition-all duration-300 hover:scale-[1.02] hover:shadow-xl hover:shadow-blue-500/10
      ${highlight ? "border-blue-500 shadow-lg shadow-blue-500/20" : "border-slate-700"}
      ${className}
    `}
  >
    {highlight && (
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-500 via-white to-blue-500" />
    )}
    <div className="p-4">
      <h3 className="text-xs uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-blue-500" />
        {title}
      </h3>
      {children}
    </div>
  </div>
);

interface StatRowProps {
  label: string;
  homeValue: number;
  awayValue: number;
  highlight?: boolean;
  format?: "number" | "rank" | "percent";
}

const StatRow = ({ label, homeValue, awayValue, highlight = false, format = "number" }: StatRowProps) => {
  const formatValue = (val: number) => {
    if (format === "rank") return `#${val}`;
    if (format === "percent") return `${val}%`;
    return val;
  };

  const homeWins = format === "rank" ? homeValue < awayValue : homeValue > awayValue;

  return (
    <div
      className={`
        flex items-center justify-between py-2 border-b border-slate-700/50 last:border-0
        ${highlight ? "bg-blue-500/10 -mx-2 px-2 rounded" : ""}
      `}
    >
      <span className={`font-mono text-lg w-20 text-right ${homeWins ? "text-green-400 font-bold" : "text-slate-300"}`}>
        {formatValue(homeValue)}
      </span>
      <span className="text-slate-500 text-sm flex-1 text-center">{label}</span>
      <span className={`font-mono text-lg w-20 text-left ${!homeWins ? "text-green-400 font-bold" : "text-slate-300"}`}>
        {formatValue(awayValue)}
      </span>
    </div>
  );
};

// ============================================================================
// CHART COMPONENTS
// ============================================================================

interface SpreadProbabilityChartProps {
  data: SpreadProbability[];
  currentSpread: number;
}

const SpreadProbabilityChart = ({ data, currentSpread }: SpreadProbabilityChartProps) => {
  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: SpreadProbability }> }) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      return (
        <div className="bg-slate-900 border border-slate-600 rounded-lg p-3 shadow-xl">
          <p className="text-white font-bold">Spread: {item.spread > 0 ? "+" : ""}{item.spread}</p>
          <p className="text-blue-400">Cover Probability: {item.probability}%</p>
          <p className={item.edge > 0 ? "text-green-400" : "text-red-400"}>
            Edge: {item.edge > 0 ? "+" : ""}{item.edge}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <DashboardCard title="Spread Coverage Probability" highlight className="col-span-1">
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="spreadGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="spread"
              stroke="#64748B"
              tick={{ fill: "#94A3B8", fontSize: 11 }}
              tickFormatter={(v) => (v > 0 ? `+${v}` : v)}
            />
            <YAxis
              stroke="#64748B"
              tick={{ fill: "#94A3B8", fontSize: 11 }}
              tickFormatter={(v) => `${v}%`}
              domain={[0, 100]}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine
              x={currentSpread}
              stroke="#EF4444"
              strokeWidth={2}
              strokeDasharray="5 5"
              label={{ value: `Current: ${currentSpread}`, fill: "#EF4444", fontSize: 11, position: "top" }}
            />
            <Area
              type="monotone"
              dataKey="probability"
              stroke="#3B82F6"
              strokeWidth={3}
              fill="url(#spreadGradient)"
              dot={{ fill: "#3B82F6", strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, fill: "#60A5FA" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 flex items-center justify-between text-sm">
        <span className="text-slate-400">
          Cover @ {currentSpread}: <span className="text-white font-bold">42%</span>
        </span>
        <EdgeBadge edge={4} threshold={5} />
      </div>
    </DashboardCard>
  );
};

interface OverUnderChartProps {
  data: OverUnderProbability[];
  currentTotal: number;
}

const OverUnderChart = ({ data, currentTotal }: OverUnderChartProps) => {
  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: OverUnderProbability }> }) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      return (
        <div className="bg-slate-900 border border-slate-600 rounded-lg p-3 shadow-xl">
          <p className="text-white font-bold">Total: {item.total}</p>
          <p className="text-green-400">Over Probability: {item.overProb}%</p>
          <p className="text-red-400">Under Probability: {item.underProb}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <DashboardCard title="Over/Under Probability" highlight className="col-span-1">
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="total" stroke="#64748B" tick={{ fill: "#94A3B8", fontSize: 11 }} />
            <YAxis
              stroke="#64748B"
              tick={{ fill: "#94A3B8", fontSize: 11 }}
              tickFormatter={(v) => `${v}%`}
              domain={[0, 100]}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine x={currentTotal} stroke="#FBBF24" strokeWidth={2} strokeDasharray="5 5" />
            <Bar dataKey="overProb" stackId="a" fill="#22C55E" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell
                  key={`cell-over-${index}`}
                  fill={entry.total === currentTotal ? "#4ADE80" : "#22C55E"}
                  opacity={entry.total === currentTotal ? 1 : 0.7}
                />
              ))}
            </Bar>
            <Bar dataKey="underProb" stackId="a" fill="#EF4444" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell
                  key={`cell-under-${index}`}
                  fill={entry.total === currentTotal ? "#F87171" : "#EF4444"}
                  opacity={entry.total === currentTotal ? 1 : 0.7}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 flex items-center justify-between text-sm">
        <div className="flex gap-4">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-green-500" />
            <span className="text-slate-400">Over: 52%</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-red-500" />
            <span className="text-slate-400">Under: 48%</span>
          </span>
        </div>
        <EdgeBadge edge={-2.1} threshold={5} />
      </div>
    </DashboardCard>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function GameDetailDashboard({
  gameData = defaultGameData,
  spreadProbabilityData = defaultSpreadProbabilityData,
  overUnderProbabilityData = defaultOverUnderProbabilityData,
  sportsbooks = defaultSportsbooks,
  teamStats = defaultTeamStats,
  edgeAnalysis = defaultEdgeAnalysis,
}: GameDetailDashboardProps) {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    setIsLoaded(true);
  }, []);

  const { homeTeam, awayTeam, currentLine } = gameData;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-red-500/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
        <AmericanFlagBackground />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <header
          className={`mb-8 transition-all duration-700 transform ${
            isLoaded ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-8"
          }`}
        >
          {/* Brand */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-red-500 via-white to-blue-500 rounded-xl flex items-center justify-center text-2xl shadow-lg">
                🦅
              </div>
              <div>
                <h1 className="text-2xl font-black tracking-tight">
                  <span className="text-red-500">SPREAD</span>
                  <span className="text-white"> EAGLE</span>
                </h1>
                <p className="text-xs text-slate-400 uppercase tracking-widest">Edge Finder</p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-slate-400">Live Odds</span>
            </div>
          </div>

          {/* Game Matchup Header */}
          <div className="relative bg-slate-800/90 backdrop-blur-sm rounded-2xl border border-slate-700 overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-500 via-white to-blue-500" />

            <div className="p-6">
              <div className="flex items-center justify-between">
                {/* Away Team */}
                <div className="flex-1 text-center">
                  <div
                    className="mb-2 transform transition-transform hover:scale-110 flex justify-center"
                    style={{ filter: "drop-shadow(0 4px 8px rgba(0,0,0,0.3))" }}
                  >
                    <img src={awayTeam.logo} alt={awayTeam.name} className="w-20 h-20 object-contain" />
                  </div>
                  {awayTeam.ranking && (
                    <span className="text-xs bg-slate-700 px-2 py-0.5 rounded-full text-slate-300">
                      #{awayTeam.ranking}
                    </span>
                  )}
                  <h2 className="text-2xl font-black mt-2" style={{ color: awayTeam.primaryColor }}>
                    {awayTeam.abbreviation}
                  </h2>
                  <p className="text-slate-400 text-sm">{awayTeam.name}</p>
                  <p className="text-slate-500 text-xs mt-1">{awayTeam.record}</p>
                </div>

                {/* Game Info Center */}
                <div className="flex-1 text-center px-8">
                  <div className="text-slate-500 text-xs uppercase tracking-wider mb-2">
                    Saturday, Nov 23 • 2:30 PM ET
                  </div>
                  <div className="text-slate-400 text-xs mb-4">{gameData.venue}</div>

                  <div className="bg-slate-900/80 rounded-xl p-4 border border-slate-600">
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <div className="text-slate-500 text-xs uppercase mb-1">Spread</div>
                        <div className="text-2xl font-black text-white">
                          {currentLine.spreadFavorite} {currentLine.spread}
                        </div>
                      </div>
                      <div className="border-x border-slate-700 px-4">
                        <div className="text-slate-500 text-xs uppercase mb-1">O/U</div>
                        <div className="text-2xl font-black text-white">{currentLine.overUnder}</div>
                      </div>
                      <div>
                        <div className="text-slate-500 text-xs uppercase mb-1">ML</div>
                        <div className="text-lg font-bold">
                          <span className="text-slate-300">{currentLine.homeMoneyline}</span>
                          <span className="text-slate-600 mx-1">/</span>
                          <span className="text-slate-300">+{currentLine.awayMoneyline}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Home Team */}
                <div className="flex-1 text-center">
                  <div
                    className="mb-2 transform transition-transform hover:scale-110 flex justify-center"
                    style={{ filter: "drop-shadow(0 4px 8px rgba(0,0,0,0.3))" }}
                  >
                    <img src={homeTeam.logo} alt={homeTeam.name} className="w-20 h-20 object-contain" />
                  </div>
                  {homeTeam.ranking && (
                    <span className="text-xs bg-slate-700 px-2 py-0.5 rounded-full text-slate-300">
                      #{homeTeam.ranking}
                    </span>
                  )}
                  <h2 className="text-2xl font-black mt-2" style={{ color: homeTeam.primaryColor }}>
                    {homeTeam.abbreviation}
                  </h2>
                  <p className="text-slate-400 text-sm">{homeTeam.name}</p>
                  <p className="text-slate-500 text-xs mt-1">{homeTeam.record}</p>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Edge Alert Banner */}
        {edgeAnalysis.spreadEdge >= 5 && (
          <div
            className={`mb-6 bg-gradient-to-r from-green-500/20 via-green-500/10 to-green-500/20
              border border-green-500/30 rounded-xl p-4 flex items-center justify-between
              transition-all duration-700 transform ${isLoaded ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-4"}`}
            style={{ transitionDelay: "200ms" }}
          >
            <div className="flex items-center gap-3">
              <span className="text-3xl">🎯</span>
              <div>
                <div className="font-bold text-green-400">Strong Edge Detected</div>
                <div className="text-sm text-slate-400">
                  +{edgeAnalysis.spreadEdge}% edge on spread • {edgeAnalysis.confidence}% model confidence
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-slate-400">Projected Final</div>
              <div className="text-xl font-black">
                <span style={{ color: homeTeam.primaryColor }}>{edgeAnalysis.projectedScore.home}</span>
                <span className="text-slate-500 mx-2">-</span>
                <span style={{ color: awayTeam.primaryColor }}>{edgeAnalysis.projectedScore.away}</span>
              </div>
            </div>
          </div>
        )}

        {/* Probability Charts */}
        <div
          className={`grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6 transition-all duration-700 transform ${
            isLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
          style={{ transitionDelay: "300ms" }}
        >
          <SpreadProbabilityChart data={spreadProbabilityData} currentSpread={currentLine.spread} />
          <OverUnderChart data={overUnderProbabilityData} currentTotal={currentLine.overUnder} />
        </div>

        {/* Stats Grid */}
        <div
          className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6 transition-all duration-700 transform ${
            isLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
          style={{ transitionDelay: "400ms" }}
        >
          {/* SP+ Ratings */}
          <DashboardCard title="SP+ Ratings" className="md:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <div className="text-center flex-1">
                <div className="text-4xl font-black text-green-400">+{teamStats.home.spPlusOverall}</div>
                <div className="text-xs text-slate-500 mt-1">{homeTeam.abbreviation}</div>
              </div>
              <div className="text-slate-600 text-2xl">vs</div>
              <div className="text-center flex-1">
                <div className="text-4xl font-black text-blue-400">+{teamStats.away.spPlusOverall}</div>
                <div className="text-xs text-slate-500 mt-1">{awayTeam.abbreviation}</div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="bg-slate-900/50 rounded-lg p-3">
                <div className="flex justify-between mb-2">
                  <span className="text-slate-400">Offense</span>
                  <span className="text-green-400 font-mono">+{teamStats.home.spPlusOffense}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Defense</span>
                  <span className="text-green-400 font-mono">+{teamStats.home.spPlusDefense}</span>
                </div>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-3">
                <div className="flex justify-between mb-2">
                  <span className="text-slate-400">Offense</span>
                  <span className="text-blue-400 font-mono">+{teamStats.away.spPlusOffense}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Defense</span>
                  <span className="text-blue-400 font-mono">+{teamStats.away.spPlusDefense}</span>
                </div>
              </div>
            </div>
          </DashboardCard>

          {/* Edge Summary */}
          <DashboardCard title="Calculated Edges" highlight>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Spread</span>
                <EdgeBadge edge={edgeAnalysis.spreadEdge} />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Over/Under</span>
                <EdgeBadge edge={edgeAnalysis.ouEdge} />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Moneyline</span>
                <EdgeBadge edge={edgeAnalysis.mlEdge} />
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-700">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">Model Confidence</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-green-500 rounded-full"
                      style={{ width: `${edgeAnalysis.confidence}%` }}
                    />
                  </div>
                  <span className="font-mono text-white">{edgeAnalysis.confidence}%</span>
                </div>
              </div>
            </div>
          </DashboardCard>

          {/* Projected Score */}
          <DashboardCard title="Model Projection">
            <div className="text-center mb-4">
              <div className="text-5xl font-black">
                <span style={{ color: homeTeam.primaryColor }}>{edgeAnalysis.projectedScore.home}</span>
                <span className="text-slate-500 mx-3">-</span>
                <span style={{ color: awayTeam.primaryColor }}>{edgeAnalysis.projectedScore.away}</span>
              </div>
              <div className="text-xs text-slate-500 mt-2">
                {homeTeam.abbreviation} vs {awayTeam.abbreviation}
              </div>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-3">
              <div className="flex justify-between items-center">
                <span className="text-slate-400 text-sm">Projected Total</span>
                <span className="text-xl font-bold text-white">{edgeAnalysis.projectedTotal}</span>
              </div>
              <div className="flex justify-between items-center mt-2">
                <span className="text-slate-400 text-sm">vs Line ({currentLine.overUnder})</span>
                <span
                  className={`text-sm font-bold ${
                    edgeAnalysis.projectedTotal > currentLine.overUnder ? "text-green-400" : "text-red-400"
                  }`}
                >
                  {edgeAnalysis.projectedTotal > currentLine.overUnder ? "OVER" : "UNDER"} +
                  {Math.abs(edgeAnalysis.projectedTotal - currentLine.overUnder).toFixed(1)}
                </span>
              </div>
            </div>
          </DashboardCard>
        </div>

        {/* Team Stats Comparison */}
        <div
          className={`grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6 transition-all duration-700 transform ${
            isLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
          style={{ transitionDelay: "500ms" }}
        >
          <DashboardCard title="Offensive Stats">
            <StatRow label="Points/Game" homeValue={teamStats.home.ppg} awayValue={teamStats.away.ppg} />
            <StatRow label="Yards/Game" homeValue={teamStats.home.yardsPg} awayValue={teamStats.away.yardsPg} />
            <StatRow label="Rush YPG" homeValue={teamStats.home.rushYpg} awayValue={teamStats.away.rushYpg} />
            <StatRow label="Pass YPG" homeValue={teamStats.home.passYpg} awayValue={teamStats.away.passYpg} />
            <StatRow
              label="3rd Down %"
              homeValue={teamStats.home.thirdDownPct}
              awayValue={teamStats.away.thirdDownPct}
              format="percent"
            />
            <StatRow
              label="Red Zone %"
              homeValue={teamStats.home.redZonePct}
              awayValue={teamStats.away.redZonePct}
              format="percent"
              highlight
            />
          </DashboardCard>

          <DashboardCard title="Defensive Stats">
            <StatRow label="Opp PPG" homeValue={teamStats.home.oppPpg} awayValue={teamStats.away.oppPpg} />
            <StatRow
              label="Off Rank"
              homeValue={teamStats.home.offenseRank}
              awayValue={teamStats.away.offenseRank}
              format="rank"
            />
            <StatRow
              label="Def Rank"
              homeValue={teamStats.home.defenseRank}
              awayValue={teamStats.away.defenseRank}
              format="rank"
              highlight
            />
          </DashboardCard>

          {/* Live Odds Comparison */}
          <DashboardCard title="Live Odds Comparison">
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {sportsbooks.map((book, idx) => (
                <div
                  key={book.name}
                  className={`flex items-center justify-between p-2 rounded-lg text-sm cursor-pointer
                    transition-colors hover:bg-slate-700/50
                    ${idx === 0 ? "bg-green-500/10 border border-green-500/30" : "bg-slate-900/50"}`}
                >
                  <div className="flex-1">
                    <div className="font-medium text-white flex items-center gap-2">
                      {book.name}
                      {idx === 0 && <span className="text-xs text-green-400">Best</span>}
                    </div>
                  </div>
                  <div className="flex gap-4 text-xs">
                    <div className="text-center">
                      <div className="text-slate-500">Spread</div>
                      <div className="font-mono text-slate-300">
                        {book.spread} ({book.spreadOdds})
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-slate-500">O/U</div>
                      <div className="font-mono text-slate-300">
                        {book.ou} ({book.ouOdds})
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-slate-500">ML</div>
                      <div className="font-mono text-slate-300">{book.ml}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </DashboardCard>
        </div>

        {/* Footer */}
        <footer
          className={`text-center text-slate-500 text-xs py-8 border-t border-slate-800 transition-all duration-700 ${
            isLoaded ? "opacity-100" : "opacity-0"
          }`}
          style={{ transitionDelay: "600ms" }}
        >
          <div className="flex items-center justify-center gap-2 mb-2">
            <span className="text-red-500">★</span>
            <span>SPREAD EAGLE</span>
            <span className="text-blue-500">★</span>
          </div>
          <p>Data updated: {new Date().toLocaleString()} • All odds subject to change</p>
          <p className="mt-1 text-slate-600">For entertainment purposes only. Please gamble responsibly.</p>
        </footer>
      </div>
    </div>
  );
}
