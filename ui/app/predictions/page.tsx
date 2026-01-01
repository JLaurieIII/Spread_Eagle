"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Prediction {
  id: number;
  gameDate: string;
  awayTeam: string;
  homeTeam: string;
  spread: number;
  pick: string;
  pickSpread: string;
  confidence: number;
  rating: string;
}

interface PredictionsResponse {
  generated: string;
  model: string;
  predictions: Prediction[];
}

function getRatingColor(rating: string) {
  switch (rating) {
    case "STRONG PLAY":
      return "bg-green-600";
    case "PLAY":
      return "bg-green-500";
    case "LEAN":
      return "bg-yellow-500";
    default:
      return "bg-gray-500";
  }
}

function getConfidenceColor(confidence: number) {
  if (confidence >= 60) return "text-green-400";
  if (confidence >= 55) return "text-yellow-400";
  return "text-gray-400";
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr + "T12:00:00");
  return date.toLocaleDateString("en-US", {
    weekday: "long",
    month: "short",
    day: "numeric",
  });
}

export default function PredictionsPage() {
  const [data, setData] = useState<PredictionsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/predictions")
      .then((res) => res.json())
      .then((data) => {
        setData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-2xl animate-pulse">Loading predictions...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-2xl text-red-500">Failed to load predictions</div>
      </div>
    );
  }

  // Group predictions by date
  const groupedByDate = data.predictions.reduce((acc, pred) => {
    if (!acc[pred.gameDate]) {
      acc[pred.gameDate] = [];
    }
    acc[pred.gameDate].push(pred);
    return acc;
  }, {} as Record<string, Prediction[]>);

  const sortedDates = Object.keys(groupedByDate).sort();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-black text-white">
      {/* Header */}
      <div className="border-b border-gray-800 bg-black/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
                SPREAD EAGLE
              </h1>
              <p className="text-gray-400 text-sm">Bowl Game Predictions</p>
            </div>
            <div className="text-right text-sm text-gray-500">
              <div>Model: {data.model}</div>
              <div>Updated: {new Date(data.generated).toLocaleString()}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Stats Summary */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="pt-6 text-center">
              <div className="text-4xl font-bold text-amber-400">
                {data.predictions.length}
              </div>
              <div className="text-gray-400 text-sm">Total Games</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="pt-6 text-center">
              <div className="text-4xl font-bold text-green-400">
                {data.predictions.filter((p) => p.rating === "PLAY").length}
              </div>
              <div className="text-gray-400 text-sm">Play-Rated</div>
            </CardContent>
          </Card>
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="pt-6 text-center">
              <div className="text-4xl font-bold text-blue-400">
                {Math.round(
                  data.predictions.reduce((sum, p) => sum + p.confidence, 0) /
                    data.predictions.length
                )}
                %
              </div>
              <div className="text-gray-400 text-sm">Avg Confidence</div>
            </CardContent>
          </Card>
        </div>

        {/* Predictions by Date */}
        {sortedDates.map((date) => (
          <div key={date} className="mb-8">
            <h2 className="text-xl font-semibold mb-4 text-gray-300 border-b border-gray-800 pb-2">
              {formatDate(date)}
            </h2>
            <div className="grid gap-4">
              {groupedByDate[date].map((game) => (
                <Card
                  key={game.id}
                  className="bg-gray-900/50 border-gray-800 hover:border-gray-700 transition-colors"
                >
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      {/* Matchup */}
                      <div className="flex-1">
                        <div className="text-lg font-medium">
                          <span className="text-gray-300">{game.awayTeam}</span>
                          <span className="text-gray-600 mx-2">@</span>
                          <span className="text-white">{game.homeTeam}</span>
                        </div>
                        <div className="text-sm text-gray-500 mt-1">
                          Line: {game.homeTeam}{" "}
                          {game.spread > 0 ? "+" : ""}
                          {game.spread}
                        </div>
                      </div>

                      {/* Pick */}
                      <div className="text-center px-8">
                        <div className="text-sm text-gray-500 mb-1">PICK</div>
                        <div className="text-xl font-bold text-amber-400">
                          {game.pick}
                        </div>
                        <div className="text-lg text-gray-300">
                          {game.pickSpread}
                        </div>
                      </div>

                      {/* Confidence & Rating */}
                      <div className="text-right">
                        <div
                          className={`text-3xl font-bold ${getConfidenceColor(
                            game.confidence
                          )}`}
                        >
                          {game.confidence}%
                        </div>
                        <Badge
                          className={`${getRatingColor(game.rating)} text-white mt-2`}
                        >
                          {game.rating}
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        ))}

        {/* Footer */}
        <div className="text-center text-gray-600 text-sm mt-12 pb-8">
          <p>Powered by XGBoost + dbt Analytics</p>
          <p className="mt-1">Bet responsibly. Past performance does not guarantee future results.</p>
        </div>
      </div>
    </div>
  );
}
