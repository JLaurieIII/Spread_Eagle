"use client";

import React, { useEffect, useMemo, useState } from "react";
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
  Loader2,
} from "lucide-react";

// API Base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

// ============================================================================
// Types (matching API response)
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
  rank?: number | null;
  confRecord: string;
  conference: string;
  atsRecord: string;
  ouRecord: string;
  recentForm: ("W" | "L")[];
  last5Games: GameResult[];
  ppg: number | null;
  oppPpg: number | null;
  pace: number | null;
};

type CBBGame = {
  id: number;
  gameDate: string;
  gameTime: string;
  venue: string;
  location: string;
  spread: string | null;
  total: string | null;
  homeTeam: TeamData;
  awayTeam: TeamData;
  league: string;
};

// Helper to format date for API (uses local timezone)
function formatDateForAPI(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

// Helper to format date for display
function formatDateForDisplay(date: Date): string {
  return date.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

// Helper to create a date in local timezone (avoids UTC issues)
function createLocalDate(year: number, month: number, day: number): Date {
  return new Date(year, month - 1, day); // month is 0-indexed in JS
}

// ============================================================================
// API Fetching
// ============================================================================

async function fetchDashboardGames(date: string): Promise<CBBGame[]> {
  const response = await fetch(`${API_BASE_URL}/cbb/dashboard?date=${date}`);
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  const data = await response.json();
  return data.games;
}

// ============================================================================
// Helper Functions
// ============================================================================

function cn(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

// ============================================================================
// Components - Patriotic Gradient Background
// ============================================================================

function FlagBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* Main gradient - navy to white to soft red */}
      <div
        className="absolute inset-0"
        style={{
          background: `linear-gradient(135deg,
            #0A1628 0%,
            #1a3a5c 15%,
            #3d5a80 25%,
            #e8e4df 40%,
            #f5f3f0 50%,
            #e8e4df 60%,
            #c9a9a9 75%,
            #b8888a 85%,
            #9e6b6d 100%
          )`,
        }}
      />

      {/* Soft white overlay for readability */}
      <div className="absolute inset-0 bg-white/30" />
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
          <div className="text-sm font-semibold text-slate-700">{game.spread ?? "TBD"}</div>
          <div className="text-xs text-slate-500">O/U {game.total ?? "TBD"}</div>
        </div>
      </div>

      {/* Time and conference */}
      <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100">
        <span className="text-xs text-slate-500">{game.gameTime}</span>
        <span className="text-xs text-slate-500">{game.homeTeam.conference}</span>
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
          <div className="text-lg font-bold text-slate-800">{team.ppg ?? "-"}</div>
        </div>
        <div className="bg-slate-50 rounded-lg p-2">
          <div className="text-xs text-slate-500 uppercase tracking-wide">OPP PPG</div>
          <div className="text-lg font-bold text-slate-800">{team.oppPpg ?? "-"}</div>
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
              <span>{game.venue}{game.location && ` • ${game.location}`}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-600 mt-1">
              <Clock className="w-4 h-4" />
              <span>{game.gameDate} • {game.gameTime}</span>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="flex items-center gap-2">
              {game.spread && (
                <div className="px-3 py-1.5 bg-slate-800 text-white text-sm font-bold rounded-lg">
                  {game.spread}
                </div>
              )}
              {game.total && (
                <div className="px-3 py-1.5 bg-slate-800 text-white text-sm font-bold rounded-lg">
                  O/U {game.total}
                </div>
              )}
            </div>
            <div className="text-xs text-slate-500">
              {game.homeTeam.conference} vs {game.awayTeam.conference}
            </div>
          </div>
        </div>
      </div>

      {/* Teams Side by Side */}
      <div className="grid md:grid-cols-2 gap-4">
        <TeamCard team={game.awayTeam} isHome={false} />
        <TeamCard team={game.homeTeam} isHome={true} />
      </div>

      {/* Trends Section */}
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
                <span className="font-bold text-slate-800">{game.awayTeam.pace ?? "-"}</span>
              </div>
              {game.awayTeam.pace && (
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-slate-800 rounded-full"
                    style={{ width: `${(game.awayTeam.pace / 80) * 100}%` }}
                  />
                </div>
              )}
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">{game.homeTeam.shortName} Pace</span>
                <span className="font-bold text-slate-800">{game.homeTeam.pace ?? "-"}</span>
              </div>
              {game.homeTeam.pace && (
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-slate-800 rounded-full"
                    style={{ width: `${(game.homeTeam.pace / 80) * 100}%` }}
                  />
                </div>
              )}
              {game.awayTeam.pace && game.homeTeam.pace && (
                <div className="text-xs text-slate-500 mt-2">
                  Combined pace suggests ~{Math.round((game.awayTeam.pace + game.homeTeam.pace) / 2)} possessions per team
                </div>
              )}
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
                  <span className="font-bold text-emerald-600">{game.awayTeam.ppg ?? "-"}</span>
                  <span className="text-slate-400 mx-1">/</span>
                  <span className="font-bold text-red-600">{game.awayTeam.oppPpg ?? "-"}</span>
                </div>
              </div>
              <div className="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                <span className="text-sm text-slate-600">{game.homeTeam.shortName}</span>
                <div className="text-right">
                  <span className="font-bold text-emerald-600">{game.homeTeam.ppg ?? "-"}</span>
                  <span className="text-slate-400 mx-1">/</span>
                  <span className="font-bold text-red-600">{game.homeTeam.oppPpg ?? "-"}</span>
                </div>
              </div>
              <div className="text-xs text-slate-500">
                PPG scored / PPG allowed
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ============================================================================
// Main Page
// ============================================================================

export default function CBBDashboard() {
  // Default to Jan 24, 2026 which has rich test data (142 games)
  // Change to new Date() for production
  const [currentDate, setCurrentDate] = useState(() => createLocalDate(2026, 1, 24));
  const [games, setGames] = useState<CBBGame[]>([]);
  const [selectedGameId, setSelectedGameId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch games when date changes
  useEffect(() => {
    async function loadGames() {
      setIsLoading(true);
      setError(null);
      try {
        const dateStr = formatDateForAPI(currentDate);
        const fetchedGames = await fetchDashboardGames(dateStr);
        setGames(fetchedGames);
        // Select first game by default
        if (fetchedGames.length > 0) {
          setSelectedGameId(fetchedGames[0].id);
        } else {
          setSelectedGameId(null);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load games");
        setGames([]);
        setSelectedGameId(null);
      } finally {
        setIsLoading(false);
      }
    }
    loadGames();
  }, [currentDate]);

  const selectedGame = useMemo(() => {
    return games.find((g) => g.id === selectedGameId) ?? null;
  }, [games, selectedGameId]);

  const handlePrevDay = () => {
    setCurrentDate((d) => {
      const newDate = new Date(d);
      newDate.setDate(newDate.getDate() - 1);
      return newDate;
    });
  };

  const handleNextDay = () => {
    setCurrentDate((d) => {
      const newDate = new Date(d);
      newDate.setDate(newDate.getDate() + 1);
      return newDate;
    });
  };

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
            <Button variant="outline" size="sm" className="bg-white/80" onClick={handlePrevDay}>
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <div className="px-3 py-1.5 bg-white/80 rounded-lg border border-slate-200 text-sm font-medium">
              <Calendar className="w-4 h-4 inline mr-2" />
              {formatDateForDisplay(currentDate)}
            </div>
            <Button variant="outline" size="sm" className="bg-white/80" onClick={handleNextDay}>
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-slate-600" />
            <span className="ml-3 text-slate-600">Loading games...</span>
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <div className="text-center py-20">
            <p className="text-red-600 mb-2">Error: {error}</p>
            <p className="text-slate-500 text-sm">Make sure the API is running on {API_BASE_URL}</p>
          </div>
        )}

        {/* No Games State */}
        {!isLoading && !error && games.length === 0 && (
          <div className="text-center py-20">
            <p className="text-slate-600">No games scheduled for {formatDateForDisplay(currentDate)}</p>
          </div>
        )}

        {/* Main Content */}
        {!isLoading && !error && games.length > 0 && (
          <div className="grid lg:grid-cols-[320px_1fr] gap-6">
            {/* Game List */}
            <div className="space-y-3 max-h-[calc(100vh-200px)] overflow-y-auto pr-2">
              <div className="text-sm font-semibold text-slate-600 uppercase tracking-wide px-1">
                Games ({games.length})
              </div>
              {games.map((game) => (
                <MiniGameTile
                  key={game.id}
                  game={game}
                  isSelected={game.id === selectedGameId}
                  onClick={() => setSelectedGameId(game.id)}
                />
              ))}
            </div>

            {/* Selected Game Detail */}
            {selectedGame && <GameDetailDashboard game={selectedGame} />}
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-slate-500">
          Spread Eagle • Probability-first sports analytics • Not financial advice
        </div>
      </div>
    </div>
  );
}
