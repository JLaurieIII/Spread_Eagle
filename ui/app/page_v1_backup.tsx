"use client";

import React, { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Activity,
  ArrowRight,
  Calendar,
  ChevronLeft,
  ChevronRight,
  MapPin,
  TrendingUp,
  TrendingDown,
  Target,
  Zap,
  BarChart3,
  Users,
  Clock,
} from "lucide-react";

// ============================================================================
// Types
// ============================================================================

type GameResult = {
  date: string;
  opponent: string;
  result: "W" | "L";
  score: string;
  spreadResult: number;
};

type TeamData = {
  name: string;
  shortName: string;
  primaryColor: string;
  record: string;
  rank?: number;
  confRecord: string;
  conference: string;
  atsRecord: string;
  ouRecord: string;
  recentForm: ("W" | "L")[];
  last5Games: GameResult[];
  avgPoints: number;
  avgPointsAllowed: number;
  pace: number; // possessions per game
};

type CBBGame = {
  id: string;
  gameDate: string;
  gameTime: string;
  venue: string;
  location: string;
  spread: string;
  spreadValue: number;
  total: number;
  homeTeam: TeamData;
  awayTeam: TeamData;
  // Analysis
  teaserFriendly: boolean;
  volatility: "LOW" | "MED" | "HIGH";
  keyFactors: string[];
  tldr: string;
};

// ============================================================================
// Mock Data - CBB Games
// ============================================================================

const mockCBBGames: CBBGame[] = [
  {
    id: "cbb-2026-tenn-ala",
    gameDate: "Sat, Jan 24",
    gameTime: "8:30 PM",
    venue: "Coleman Coliseum",
    location: "Tuscaloosa, AL",
    spread: "ALA -3.5",
    spreadValue: -3.5,
    total: 167.5,
    teaserFriendly: true,
    volatility: "MED",
    keyFactors: [
      "Tennessee's defense ranks #8 nationally in adjusted efficiency",
      "Alabama shooting 38% from 3 in SEC play",
      "Both teams above average pace - expect 75+ possessions",
      "Tennessee 2-5 ATS as road underdogs this season",
    ],
    tldr: "High-pace SEC battle between two tournament teams. Tennessee's elite defense travels, but Alabama's home court and 3-point shooting could be the difference. Total feels about right given both teams' pace preferences.",
    awayTeam: {
      name: "Tennessee",
      shortName: "TENN",
      primaryColor: "#FF8200",
      record: "12-6",
      rank: 12,
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
      avgPoints: 78.2,
      avgPointsAllowed: 68.4,
      pace: 71.2,
    },
    homeTeam: {
      name: "Alabama",
      shortName: "ALA",
      primaryColor: "#9E1B32",
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
      avgPoints: 84.6,
      avgPointsAllowed: 74.2,
      pace: 74.8,
    },
  },
  {
    id: "cbb-2026-duke-unc",
    gameDate: "Sat, Jan 24",
    gameTime: "6:00 PM",
    venue: "Cameron Indoor Stadium",
    location: "Durham, NC",
    spread: "DUKE -6.5",
    spreadValue: -6.5,
    total: 158.5,
    teaserFriendly: false,
    volatility: "HIGH",
    keyFactors: [
      "Rivalry game - throw out the records",
      "Duke 8-2 at home this season",
      "UNC struggling with turnovers (15.2 per game)",
      "Cameron Indoor historically tough for visitors",
    ],
    tldr: "Classic rivalry where anything can happen. Duke's home court is elite but UNC always shows up for this one. High variance game - not ideal for teasers.",
    awayTeam: {
      name: "North Carolina",
      shortName: "UNC",
      primaryColor: "#7BAFD4",
      record: "11-7",
      rank: 18,
      confRecord: "3-3",
      conference: "ACC",
      atsRecord: "8-10",
      ouRecord: "10-8",
      recentForm: ["L", "W", "L", "W", "W"],
      last5Games: [
        { date: "1/4", opponent: "Wake Forest", result: "L", score: "68-72", spreadResult: -8 },
        { date: "1/8", opponent: "NC State", result: "W", score: "82-76", spreadResult: 2 },
        { date: "1/11", opponent: "Virginia", result: "L", score: "61-58", spreadResult: -7 },
        { date: "1/15", opponent: "Clemson", result: "W", score: "79-71", spreadResult: 4 },
        { date: "1/20", opponent: "Boston College", result: "W", score: "88-65", spreadResult: 8 },
      ],
      avgPoints: 74.8,
      avgPointsAllowed: 71.2,
      pace: 68.5,
    },
    homeTeam: {
      name: "Duke",
      shortName: "DUKE",
      primaryColor: "#003087",
      record: "15-3",
      rank: 5,
      confRecord: "5-1",
      conference: "ACC",
      atsRecord: "9-9",
      ouRecord: "8-10",
      recentForm: ["W", "W", "W", "L", "W"],
      last5Games: [
        { date: "1/4", opponent: "Pittsburgh", result: "W", score: "76-62", spreadResult: 2 },
        { date: "1/7", opponent: "Syracuse", result: "W", score: "84-71", spreadResult: -1 },
        { date: "1/11", opponent: "Louisville", result: "W", score: "78-65", spreadResult: 0 },
        { date: "1/14", opponent: "Miami", result: "L", score: "72-74", spreadResult: -12 },
        { date: "1/18", opponent: "Georgia Tech", result: "W", score: "81-68", spreadResult: 1 },
      ],
      avgPoints: 79.4,
      avgPointsAllowed: 66.8,
      pace: 69.2,
    },
  },
  {
    id: "cbb-2026-kansas-baylor",
    gameDate: "Sat, Jan 24",
    gameTime: "4:00 PM",
    venue: "Allen Fieldhouse",
    location: "Lawrence, KS",
    spread: "KU -4.5",
    spreadValue: -4.5,
    total: 149.5,
    teaserFriendly: true,
    volatility: "LOW",
    keyFactors: [
      "Kansas 12-0 at Allen Fieldhouse",
      "Both teams play slow, methodical basketball",
      "Baylor ranks #3 in defensive efficiency",
      "Low turnover teams - clean possession game",
    ],
    tldr: "Two elite defenses in a rock fight. Kansas home court gives them the edge but Baylor can grind with anyone. Under looks appealing given both teams' defensive profiles.",
    awayTeam: {
      name: "Baylor",
      shortName: "BAY",
      primaryColor: "#154734",
      record: "13-5",
      rank: 8,
      confRecord: "4-2",
      conference: "Big 12",
      atsRecord: "10-8",
      ouRecord: "7-11",
      recentForm: ["W", "W", "L", "W", "W"],
      last5Games: [
        { date: "1/4", opponent: "TCU", result: "W", score: "68-62", spreadResult: 1 },
        { date: "1/8", opponent: "Texas Tech", result: "W", score: "71-65", spreadResult: 3 },
        { date: "1/11", opponent: "Iowa State", result: "L", score: "58-64", spreadResult: -4 },
        { date: "1/15", opponent: "UCF", result: "W", score: "72-61", spreadResult: 2 },
        { date: "1/20", opponent: "Oklahoma State", result: "W", score: "65-58", spreadResult: -1 },
      ],
      avgPoints: 71.2,
      avgPointsAllowed: 62.8,
      pace: 64.8,
    },
    homeTeam: {
      name: "Kansas",
      shortName: "KU",
      primaryColor: "#0051BA",
      record: "14-4",
      rank: 4,
      confRecord: "5-1",
      conference: "Big 12",
      atsRecord: "11-7",
      ouRecord: "6-12",
      recentForm: ["W", "W", "W", "W", "L"],
      last5Games: [
        { date: "1/4", opponent: "West Virginia", result: "W", score: "75-68", spreadResult: -2 },
        { date: "1/7", opponent: "Cincinnati", result: "W", score: "78-71", spreadResult: 1 },
        { date: "1/11", opponent: "Houston", result: "W", score: "65-62", spreadResult: -5 },
        { date: "1/15", opponent: "BYU", result: "W", score: "82-74", spreadResult: 3 },
        { date: "1/18", opponent: "Arizona", result: "L", score: "71-78", spreadResult: -9 },
      ],
      avgPoints: 76.8,
      avgPointsAllowed: 65.4,
      pace: 66.4,
    },
  },
];

// ============================================================================
// Helper Functions
// ============================================================================

function cn(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

// ============================================================================
// Components - Flag Background
// ============================================================================

function FlagBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* Stars field */}
      <div className="absolute -left-20 -top-20 h-72 w-72 rounded-[3rem] bg-slate-900/90 shadow-2xl" />
      <div className="absolute left-4 top-6 grid grid-cols-8 gap-1.5 opacity-60">
        {Array.from({ length: 48 }).map((_, i) => (
          <div key={i} className="h-1.5 w-1.5 rounded-full bg-white/80" />
        ))}
      </div>

      {/* Stripes */}
      <div className="absolute -right-64 top-0 h-[800px] w-[1000px] rotate-3 overflow-hidden rounded-[3rem]">
        {Array.from({ length: 13 }).map((_, i) => (
          <div
            key={i}
            className={cn("h-[7.69%]", i % 2 === 0 ? "bg-red-600/15" : "bg-white/5")}
          />
        ))}
      </div>

      {/* Vignette */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-50/5 via-transparent to-slate-100/30" />
    </div>
  );
}

// ============================================================================
// Components - Mini Game Tile (for game list)
// ============================================================================

function MiniGameTile({
  game,
  isSelected,
  onClick,
}: {
  game: CBBGame;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full rounded-xl border p-3 text-left transition-all duration-200",
        isSelected
          ? "border-slate-800 bg-white shadow-lg scale-[1.02]"
          : "border-slate-200 bg-white/60 hover:bg-white hover:shadow-md hover:scale-[1.01]"
      )}
    >
      {/* Teams */}
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            {game.awayTeam.rank && (
              <span className="text-xs font-bold text-slate-500">#{game.awayTeam.rank}</span>
            )}
            <span className="font-bold text-slate-800">{game.awayTeam.shortName}</span>
            <span className="text-sm text-slate-500">{game.awayTeam.record}</span>
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            {game.homeTeam.rank && (
              <span className="text-xs font-bold text-slate-500">#{game.homeTeam.rank}</span>
            )}
            <span className="font-bold text-slate-800">{game.homeTeam.shortName}</span>
            <span className="text-sm text-slate-500">{game.homeTeam.record}</span>
          </div>
        </div>

        {/* Lines */}
        <div className="text-right">
          <div className="text-sm font-semibold text-slate-700">{game.spread}</div>
          <div className="text-xs text-slate-500">O/U {game.total}</div>
        </div>
      </div>

      {/* Time and indicators */}
      <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100">
        <span className="text-xs text-slate-500">{game.gameTime}</span>
        <div className="flex items-center gap-2">
          {game.teaserFriendly && (
            <span className="text-xs px-1.5 py-0.5 bg-emerald-100 text-emerald-700 rounded font-medium">
              Teaser ✓
            </span>
          )}
          <span
            className={cn(
              "text-xs px-1.5 py-0.5 rounded font-medium",
              game.volatility === "LOW" && "bg-blue-100 text-blue-700",
              game.volatility === "MED" && "bg-amber-100 text-amber-700",
              game.volatility === "HIGH" && "bg-red-100 text-red-700"
            )}
          >
            {game.volatility} Vol
          </span>
        </div>
      </div>
    </button>
  );
}

// ============================================================================
// Components - Team Card (detailed view)
// ============================================================================

function TeamCard({ team, isHome }: { team: TeamData; isHome: boolean }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white/80 p-4">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div
          className="w-12 h-12 rounded-full flex items-center justify-center text-2xl font-black"
          style={{
            backgroundColor: team.primaryColor + "20",
            color: team.primaryColor,
            fontFamily: "Georgia, serif",
          }}
        >
          {team.shortName.charAt(0)}
        </div>
        <div>
          <div className="flex items-center gap-2">
            {team.rank && (
              <span className="text-sm font-bold text-slate-500">#{team.rank}</span>
            )}
            <span
              className="text-lg font-bold"
              style={{ color: team.primaryColor }}
            >
              {team.name}
            </span>
          </div>
          <div className="text-sm text-slate-600">
            {team.record} • {team.confRecord} {team.conference}
          </div>
        </div>
        <Badge variant="secondary" className="ml-auto">
          {isHome ? "HOME" : "AWAY"}
        </Badge>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-slate-50 rounded-lg p-2">
          <div className="text-xs text-slate-500 uppercase tracking-wide">ATS</div>
          <div className="text-lg font-bold text-slate-800">{team.atsRecord}</div>
        </div>
        <div className="bg-slate-50 rounded-lg p-2">
          <div className="text-xs text-slate-500 uppercase tracking-wide">O/U</div>
          <div className="text-lg font-bold text-slate-800">{team.ouRecord}</div>
        </div>
        <div className="bg-slate-50 rounded-lg p-2">
          <div className="text-xs text-slate-500 uppercase tracking-wide">PPG</div>
          <div className="text-lg font-bold text-slate-800">{team.avgPoints}</div>
        </div>
        <div className="bg-slate-50 rounded-lg p-2">
          <div className="text-xs text-slate-500 uppercase tracking-wide">OPP PPG</div>
          <div className="text-lg font-bold text-slate-800">{team.avgPointsAllowed}</div>
        </div>
      </div>

      {/* Recent Form */}
      <div className="mb-4">
        <div className="text-xs text-slate-500 uppercase tracking-wide mb-2">Recent Form</div>
        <div className="flex items-center gap-1.5">
          {team.recentForm.map((result, i) => (
            <div
              key={i}
              className={cn(
                "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white",
                result === "W" ? "bg-emerald-500" : "bg-red-500"
              )}
            >
              {result}
            </div>
          ))}
        </div>
      </div>

      {/* Last 5 Games */}
      <div>
        <div className="text-xs text-slate-500 uppercase tracking-wide mb-2">Last 5 Games</div>
        <div className="space-y-1">
          {team.last5Games.map((game, i) => (
            <div
              key={i}
              className="flex items-center justify-between text-sm py-1 border-b border-slate-100 last:border-0"
            >
              <div className="flex items-center gap-2">
                <span className="text-slate-400 w-8">{game.date}</span>
                <span className="text-slate-600">{game.opponent}</span>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "font-bold",
                    game.result === "W" ? "text-emerald-600" : "text-red-600"
                  )}
                >
                  {game.result}
                </span>
                <span className="text-slate-600">{game.score}</span>
                <span
                  className={cn(
                    "font-semibold text-xs px-1.5 py-0.5 rounded",
                    game.spreadResult > 0
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-red-100 text-red-700"
                  )}
                >
                  {game.spreadResult > 0 ? "+" : ""}
                  {game.spreadResult}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Components - Game Detail Dashboard
// ============================================================================

function GameDetailDashboard({ game }: { game: CBBGame }) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="rounded-xl bg-white/80 border border-slate-200 p-4">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h2 className="text-xl font-bold text-slate-800">
                {game.awayTeam.shortName} @ {game.homeTeam.shortName}
              </h2>
              <Badge className="bg-slate-800">CBB</Badge>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <MapPin className="w-4 h-4" />
              <span>{game.venue} • {game.location}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-600 mt-1">
              <Clock className="w-4 h-4" />
              <span>{game.gameDate} • {game.gameTime}</span>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="flex items-center gap-2">
              <div className="px-3 py-1.5 bg-slate-800 text-white text-sm font-bold rounded-lg">
                {game.spread}
              </div>
              <div className="px-3 py-1.5 bg-slate-800 text-white text-sm font-bold rounded-lg">
                O/U {game.total}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {game.teaserFriendly && (
                <Badge className="bg-emerald-600">Teaser Friendly</Badge>
              )}
              <Badge
                className={cn(
                  game.volatility === "LOW" && "bg-blue-600",
                  game.volatility === "MED" && "bg-amber-600",
                  game.volatility === "HIGH" && "bg-red-600"
                )}
              >
                {game.volatility} Volatility
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Teams Side by Side */}
      <div className="grid md:grid-cols-2 gap-4">
        <TeamCard team={game.awayTeam} isHome={false} />
        <TeamCard team={game.homeTeam} isHome={true} />
      </div>

      {/* Analysis Section */}
      <Tabs defaultValue="summary" className="w-full">
        <TabsList className="bg-white/60">
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="factors">Key Factors</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="mt-3">
          <Card className="bg-white/80">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Target className="w-4 h-4" />
                TL;DR
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-700 leading-relaxed">{game.tldr}</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="factors" className="mt-3">
          <Card className="bg-white/80">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Zap className="w-4 h-4" />
                Key Factors
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {game.keyFactors.map((factor, i) => (
                  <li key={i} className="flex items-start gap-2 text-slate-700">
                    <span className="text-slate-400 mt-1">•</span>
                    <span>{factor}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="mt-3">
          <div className="grid md:grid-cols-2 gap-4">
            <Card className="bg-white/80">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <BarChart3 className="w-4 h-4" />
                  Pace Profile
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">{game.awayTeam.shortName} Pace</span>
                    <span className="font-bold text-slate-800">{game.awayTeam.pace}</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-slate-800 rounded-full"
                      style={{ width: `${(game.awayTeam.pace / 80) * 100}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">{game.homeTeam.shortName} Pace</span>
                    <span className="font-bold text-slate-800">{game.homeTeam.pace}</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-slate-800 rounded-full"
                      style={{ width: `${(game.homeTeam.pace / 80) * 100}%` }}
                    />
                  </div>
                  <div className="text-xs text-slate-500 mt-2">
                    Combined pace suggests ~{Math.round((game.awayTeam.pace + game.homeTeam.pace) / 2)} possessions per team
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/80">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Activity className="w-4 h-4" />
                  Scoring Efficiency
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                    <span className="text-sm text-slate-600">{game.awayTeam.shortName}</span>
                    <div className="text-right">
                      <span className="font-bold text-emerald-600">{game.awayTeam.avgPoints}</span>
                      <span className="text-slate-400 mx-1">/</span>
                      <span className="font-bold text-red-600">{game.awayTeam.avgPointsAllowed}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                    <span className="text-sm text-slate-600">{game.homeTeam.shortName}</span>
                    <div className="text-right">
                      <span className="font-bold text-emerald-600">{game.homeTeam.avgPoints}</span>
                      <span className="text-slate-400 mx-1">/</span>
                      <span className="font-bold text-red-600">{game.homeTeam.avgPointsAllowed}</span>
                    </div>
                  </div>
                  <div className="text-xs text-slate-500">
                    PPG scored / PPG allowed
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ============================================================================
// Main Page
// ============================================================================

export default function CBBDashboard() {
  const [selectedGameId, setSelectedGameId] = useState(mockCBBGames[0].id);

  const selectedGame = useMemo(() => {
    return mockCBBGames.find((g) => g.id === selectedGameId) ?? mockCBBGames[0];
  }, [selectedGameId]);

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-50">
      <FlagBackground />

      <div className="relative z-10 mx-auto max-w-7xl px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-white/80 rounded-xl shadow-sm border border-slate-200">
              <span className="text-lg font-bold text-slate-800" style={{ fontFamily: "Georgia, serif" }}>
                Spread Eagle
              </span>
              <span className="text-slate-400">•</span>
              <span className="text-sm text-slate-600">CBB Dashboard</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="bg-white/80">
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <div className="px-3 py-1.5 bg-white/80 rounded-lg border border-slate-200 text-sm font-medium">
              <Calendar className="w-4 h-4 inline mr-2" />
              Sat, Jan 24
            </div>
            <Button variant="outline" size="sm" className="bg-white/80">
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid lg:grid-cols-[320px_1fr] gap-6">
          {/* Game List */}
          <div className="space-y-3">
            <div className="text-sm font-semibold text-slate-600 uppercase tracking-wide px-1">
              Today's Games ({mockCBBGames.length})
            </div>
            {mockCBBGames.map((game) => (
              <MiniGameTile
                key={game.id}
                game={game}
                isSelected={game.id === selectedGameId}
                onClick={() => setSelectedGameId(game.id)}
              />
            ))}
          </div>

          {/* Selected Game Detail */}
          <GameDetailDashboard game={selectedGame} />
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-slate-500">
          Spread Eagle • Probability-first sports analytics • Not financial advice
        </div>
      </div>
    </div>
  );
}
