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
import SpreadEaglePreview from "@/components/game-detail/SpreadEaglePreview";

// API Base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ============================================================================
// Types (matching API response)
// ============================================================================

type GameResult = {
  date: string;
  opponent: string;
  isHome: boolean;
  result: "W" | "L";
  score: string;
  spread: number | null;
  total: number | null;
  spreadResult: number;
  ouResult?: "O" | "U" | "P" | null;
  totalMargin: number | null;
};

type TeaserProfile = {
  teaser8SurvivalRate: number | null;
  teaser10SurvivalRate: number | null;
  within5Rate: number | null;
  within7Rate: number | null;
  within10Rate: number | null;
  blowoutRate: number | null;
  worstCover: number | null;
  coverStddev: number | null;
};

type OverUnderProfile = {
  overRateL10: number | null;
  underRateL10: number | null;
  avgTotalMarginL10: number | null;
  avgGameTotalL10: number | null;
  oversLast3: number | null;
  undersLast3: number | null;
  // Tightness to total metrics
  within5TotalRate: number | null;
  within7TotalRate: number | null;
  within10TotalRate: number | null;
};

// Distribution data for KDE visualization
type DistributionData = {
  margins: number[];
  mean: number;
  median: number;
  std: number;
  iqr: number;
  p5: number;
  p25: number;
  p75: number;
  p95: number;
  minVal: number;
  maxVal: number;
  within8Rate: number;
  within10Rate: number;
  skewness: number;
  predictability: number;
};

type TeamData = {
  name: string;
  shortName: string;
  primaryColor: string;
  secondaryColor: string;
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
  // Market variance
  spreadVarianceBucket: number;
  totalVarianceBucket: number;
  spreadVarianceLabel: string;
  totalVarianceLabel: string;
  archetype: string;
  spreadMeanError: number;
  totalMeanError: number;
  totalRmsStabilized: number;
  // Teaser profile (historical spread stability)
  teaserProfile: TeaserProfile | null;
  // Over/Under profile (historical O/U trends)
  overUnderProfile: OverUnderProfile | null;
  // Distribution data for KDE graphs
  spreadDistribution: DistributionData | null;
  totalDistribution: DistributionData | null;
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
  // Chaos / teaser
  chaosRating: number;
  chaosLabel: "STABLE" | "MODERATE" | "VOLATILE";
  teaserUnder8Prob: number | null;
  teaserUnder10Prob: number | null;
  edgeSummary: string[];
  // Combined historical teaser metrics
  combinedTeaser8Rate: number | null;
  combinedTeaser10Rate: number | null;
  combinedWithin10Rate: number | null;
  // Combined historical O/U metrics
  combinedOverRateL10: number | null;
  combinedUnderRateL10: number | null;
  combinedAvgTotalMargin: number | null;
  combinedWithin10TotalRate: number | null;
  // Spread Eagle predictability scores
  spreadPredictability: number | null;
  totalPredictability: number | null;
  spreadEagleScore: number | null;
  spreadEagleVerdict: string;
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

function getChaosColor(label: string) {
  switch (label) {
    case "STABLE":
      return { bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-300" };
    case "MODERATE":
      return { bg: "bg-amber-100", text: "text-amber-700", border: "border-amber-300" };
    case "VOLATILE":
      return { bg: "bg-red-100", text: "text-red-700", border: "border-red-300" };
    default:
      return { bg: "bg-slate-100", text: "text-slate-700", border: "border-slate-300" };
  }
}

function getTeaserColor(prob: number | null) {
  if (prob == null) return "text-slate-400";
  if (prob >= 0.9) return "text-emerald-600";
  if (prob >= 0.8) return "text-amber-600";
  return "text-red-600";
}

function getTeaserBg(prob: number | null) {
  if (prob == null) return "bg-slate-50";
  if (prob >= 0.9) return "bg-emerald-50";
  if (prob >= 0.8) return "bg-amber-50";
  return "bg-red-50";
}

function getArchetypeStyle(archetype: string) {
  switch (archetype) {
    case "Market Follower":
      return "bg-emerald-100 text-emerald-700 border-emerald-300";
    case "Chaos Team":
      return "bg-red-100 text-red-700 border-red-300";
    default:
      return "bg-slate-100 text-slate-600 border-slate-300";
  }
}

function getVarianceLabelColor(label: string) {
  switch (label) {
    case "LOW":
      return "text-emerald-600";
    case "HIGH":
      return "text-red-600";
    default:
      return "text-amber-600";
  }
}

// ============================================================================
// KDE Graph Component (for distribution visualization)
// ============================================================================

function KDEGraph({
  margins,
  mean,
  std,
  predictability,
  color,
  label,
  showZones = true,
}: {
  margins: number[];
  mean: number;
  std: number;
  predictability: number;
  color: string;
  label: string;
  showZones?: boolean;
}) {
  // Generate KDE curve using Gaussian kernel
  const bandwidth = std * 0.5 || 5;
  const xMin = -30;
  const xMax = 30;
  const points = 60;
  const xValues = Array.from({ length: points }, (_, i) => xMin + (i * (xMax - xMin)) / (points - 1));

  // Gaussian kernel function
  const gaussian = (x: number, xi: number) =>
    Math.exp(-0.5 * Math.pow((x - xi) / bandwidth, 2)) / (bandwidth * Math.sqrt(2 * Math.PI));

  // Calculate KDE values
  const yValues = xValues.map((x) => {
    if (margins.length === 0) return 0;
    return margins.reduce((sum, xi) => sum + gaussian(x, xi), 0) / margins.length;
  });

  const maxY = Math.max(...yValues, 0.001);

  // SVG dimensions - larger for better visibility
  const width = 340;
  const height = 120;
  const padding = { top: 12, right: 12, bottom: 28, left: 12 };
  const graphWidth = width - padding.left - padding.right;
  const graphHeight = height - padding.top - padding.bottom;

  // Scale functions
  const scaleX = (x: number) => padding.left + ((x - xMin) / (xMax - xMin)) * graphWidth;
  const scaleY = (y: number) => padding.top + graphHeight - (y / maxY) * graphHeight;

  // Generate path
  const pathData = yValues
    .map((y, i) => {
      const x = xValues[i];
      return `${i === 0 ? "M" : "L"} ${scaleX(x)} ${scaleY(y)}`;
    })
    .join(" ");

  // Fill path (closed polygon)
  const fillPath = pathData + ` L ${scaleX(xMax)} ${scaleY(0)} L ${scaleX(xMin)} ${scaleY(0)} Z`;

  // Zone boundaries
  const zone8 = scaleX(8);
  const zoneNeg8 = scaleX(-8);
  const zone10 = scaleX(10);
  const zoneNeg10 = scaleX(-10);

  // Predictability color
  const predColor = predictability >= 60 ? "#22c55e" : predictability >= 50 ? "#eab308" : "#ef4444";

  return (
    <div className="rounded-lg p-3" style={{ backgroundColor: "rgba(255,255,255,0.95)" }}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold" style={{ color: "#1e293b" }}>{label}</span>
        <div className="flex items-center gap-3">
          <span className="text-sm" style={{ color: "#64748b" }}>σ={std.toFixed(1)}</span>
          <span
            className="text-sm font-bold px-2 py-0.5 rounded"
            style={{ backgroundColor: predColor + "20", color: predColor }}
          >
            {predictability.toFixed(0)}
          </span>
        </div>
      </div>
      <svg width={width} height={height} className="overflow-visible">
        {/* Safe zones */}
        {showZones && (
          <>
            {/* Within 10 zone (lighter) */}
            <rect
              x={zoneNeg10}
              y={padding.top}
              width={zone10 - zoneNeg10}
              height={graphHeight}
              fill="#22c55e"
              opacity={0.08}
            />
            {/* Within 8 zone (darker) */}
            <rect
              x={zoneNeg8}
              y={padding.top}
              width={zone8 - zoneNeg8}
              height={graphHeight}
              fill="#22c55e"
              opacity={0.12}
            />
          </>
        )}

        {/* Zero line */}
        <line
          x1={scaleX(0)}
          y1={padding.top}
          x2={scaleX(0)}
          y2={padding.top + graphHeight}
          stroke="#1e293b"
          strokeOpacity={0.4}
          strokeWidth={1.5}
          strokeDasharray="4,4"
        />

        {/* KDE fill */}
        <path d={fillPath} fill={color} fillOpacity={0.2} />

        {/* KDE line */}
        <path d={pathData} fill="none" stroke={color} strokeWidth={2.5} />

        {/* Mean marker */}
        <circle cx={scaleX(mean)} cy={scaleY(yValues[Math.round(((mean - xMin) / (xMax - xMin)) * (points - 1))] || 0)} r={4} fill={color} />

        {/* X-axis */}
        <line
          x1={padding.left}
          y1={padding.top + graphHeight}
          x2={padding.left + graphWidth}
          y2={padding.top + graphHeight}
          stroke="#1e293b"
          strokeOpacity={0.3}
          strokeWidth={1.5}
        />

        {/* X-axis labels */}
        {[-20, -10, 0, 10, 20].map((tick) => (
          <g key={tick}>
            <text
              x={scaleX(tick)}
              y={height - 4}
              textAnchor="middle"
              style={{ fill: "#1e293b", fontSize: "13px", fontWeight: 600, fontFamily: "'Segoe UI', sans-serif" }}
            >
              {tick > 0 ? "+" : ""}{tick}
            </text>
          </g>
        ))}
      </svg>
      <div className="flex justify-center gap-3 mt-2 text-xs" style={{ color: "#64748b" }}>
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: "#22c55e40" }}></span>
          Safe zone (±10)
        </span>
      </div>
    </div>
  );
}

// ============================================================================
// KDE Comparison Component (overlaid distributions for both teams)
// ============================================================================

function KDEComparison({
  awayDist,
  homeDist,
  awayColor,
  homeColor,
  awayName,
  homeName,
  combinedScore,
  title,
}: {
  awayDist: DistributionData | null;
  homeDist: DistributionData | null;
  awayColor: string;
  homeColor: string;
  awayName: string;
  homeName: string;
  combinedScore: number | null;
  title: string;
}) {
  if (!awayDist || !homeDist || awayDist.margins.length < 5 || homeDist.margins.length < 5) {
    return null;
  }

  // Generate KDE curves for both teams
  const generateKDE = (margins: number[], std: number) => {
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

    return { xValues, yValues };
  };

  const awayKDE = generateKDE(awayDist.margins, awayDist.std);
  const homeKDE = generateKDE(homeDist.margins, homeDist.std);

  const maxY = Math.max(...awayKDE.yValues, ...homeKDE.yValues, 0.001);

  // SVG dimensions
  const width = 400;
  const height = 140;
  const padding = { top: 15, right: 15, bottom: 30, left: 15 };
  const graphWidth = width - padding.left - padding.right;
  const graphHeight = height - padding.top - padding.bottom;

  const xMin = -30;
  const xMax = 30;

  const scaleX = (x: number) => padding.left + ((x - xMin) / (xMax - xMin)) * graphWidth;
  const scaleY = (y: number) => padding.top + graphHeight - (y / maxY) * graphHeight;

  // Generate paths
  const generatePath = (kde: { xValues: number[]; yValues: number[] }) =>
    kde.yValues.map((y, i) => `${i === 0 ? "M" : "L"} ${scaleX(kde.xValues[i])} ${scaleY(y)}`).join(" ");

  const generateFillPath = (kde: { xValues: number[]; yValues: number[] }) =>
    generatePath(kde) + ` L ${scaleX(xMax)} ${scaleY(0)} L ${scaleX(xMin)} ${scaleY(0)} Z`;

  // Zone boundaries
  const zone10 = scaleX(10);
  const zoneNeg10 = scaleX(-10);

  // Combined score color
  const scoreColor = combinedScore != null
    ? combinedScore >= 60 ? "#22c55e" : combinedScore >= 50 ? "#eab308" : "#ef4444"
    : "#94a3b8";

  return (
    <Card className="bg-white/80">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center justify-between">
          <span className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            {title}
          </span>
          {combinedScore != null && (
            <span
              className="text-sm font-bold px-2 py-0.5 rounded"
              style={{ backgroundColor: scoreColor + "20", color: scoreColor }}
            >
              Combined: {combinedScore.toFixed(0)}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <svg width={width} height={height} className="mx-auto overflow-visible">
          {/* Safe zone */}
          <rect
            x={zoneNeg10}
            y={padding.top}
            width={zone10 - zoneNeg10}
            height={graphHeight}
            fill="#22c55e"
            opacity={0.1}
          />

          {/* Zero line */}
          <line
            x1={scaleX(0)}
            y1={padding.top}
            x2={scaleX(0)}
            y2={padding.top + graphHeight}
            stroke="#94a3b8"
            strokeWidth={1}
            strokeDasharray="3,3"
          />

          {/* Away team fill */}
          <path d={generateFillPath(awayKDE)} fill={awayColor} fillOpacity={0.15} />
          {/* Home team fill */}
          <path d={generateFillPath(homeKDE)} fill={homeColor} fillOpacity={0.15} />

          {/* Away team line */}
          <path d={generatePath(awayKDE)} fill="none" stroke={awayColor} strokeWidth={2.5} />
          {/* Home team line */}
          <path d={generatePath(homeKDE)} fill="none" stroke={homeColor} strokeWidth={2.5} />

          {/* X-axis */}
          <line
            x1={padding.left}
            y1={padding.top + graphHeight}
            x2={padding.left + graphWidth}
            y2={padding.top + graphHeight}
            stroke="#cbd5e1"
            strokeWidth={1}
          />

          {/* X-axis labels */}
          {[-20, -10, 0, 10, 20].map((tick) => (
            <text
              key={tick}
              x={scaleX(tick)}
              y={height - 8}
              textAnchor="middle"
              className="text-[10px] fill-slate-400"
            >
              {tick > 0 ? "+" : ""}{tick}
            </text>
          ))}
        </svg>

        {/* Legend */}
        <div className="flex justify-center gap-6 mt-2 text-sm">
          <span className="flex items-center gap-2">
            <span className="w-4 h-1 rounded" style={{ backgroundColor: awayColor }}></span>
            <span className="text-slate-600">{awayName}</span>
            <span className="text-slate-400 text-xs">(σ={awayDist.std.toFixed(1)})</span>
          </span>
          <span className="flex items-center gap-2">
            <span className="w-4 h-1 rounded" style={{ backgroundColor: homeColor }}></span>
            <span className="text-slate-600">{homeName}</span>
            <span className="text-slate-400 text-xs">(σ={homeDist.std.toFixed(1)})</span>
          </span>
        </div>

        {/* Interpretation */}
        <div className="mt-3 text-xs text-center text-slate-500">
          {combinedScore != null && combinedScore >= 60 && (
            <span className="text-emerald-600 font-medium">
              Both teams have tight distributions — strong teaser candidate
            </span>
          )}
          {combinedScore != null && combinedScore >= 50 && combinedScore < 60 && (
            <span className="text-amber-600 font-medium">
              Moderate predictability — teaser viable with caution
            </span>
          )}
          {combinedScore != null && combinedScore < 50 && (
            <span className="text-red-600 font-medium">
              Wide distributions — higher variance, avoid teasers
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Components - Patriotic Gradient Background Options
// ============================================================================

// OPTION 1: Eagle Watermark - Large faded logo in the background (FIXED position)
function FlagBackgroundEagleWatermark() {
  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden z-0">
      {/* Base gradient */}
      <div
        className="absolute inset-0"
        style={{
          background: `linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%)`,
        }}
      />

      {/* Giant faded eagle watermark - FIXED so it stays while scrolling */}
      <div
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] md:w-[1400px] md:h-[1400px]"
        style={{
          backgroundImage: "url('/logo.jpeg')",
          backgroundSize: "contain",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
          opacity: 0.05,
          filter: "grayscale(20%)",
        }}
      />

      {/* Subtle patriotic tint overlay */}
      <div
        className="absolute inset-0"
        style={{
          background: `linear-gradient(135deg,
            rgba(30, 58, 138, 0.03) 0%,
            transparent 40%,
            transparent 60%,
            rgba(185, 28, 28, 0.03) 100%
          )`,
        }}
      />
    </div>
  );
}

// OPTION 2: Stars and Subtle Stripes
function FlagBackgroundStarsStripes() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* Base white */}
      <div className="absolute inset-0 bg-slate-50" />

      {/* Diagonal stripes */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `repeating-linear-gradient(
            -45deg,
            #B91C1C,
            #B91C1C 20px,
            transparent 20px,
            transparent 40px,
            #1E3A8A 40px,
            #1E3A8A 60px,
            transparent 60px,
            transparent 80px
          )`,
        }}
      />

      {/* Star field in corner */}
      <div className="absolute top-0 left-0 w-1/3 h-1/2">
        {[...Array(15)].map((_, i) => (
          <div
            key={i}
            className="absolute text-[#1E3A8A]"
            style={{
              top: `${10 + Math.random() * 80}%`,
              left: `${10 + Math.random() * 80}%`,
              opacity: 0.06 + Math.random() * 0.04,
              fontSize: `${12 + Math.random() * 16}px`,
            }}
          >
            ★
          </div>
        ))}
      </div>

      {/* Soft vignette */}
      <div
        className="absolute inset-0"
        style={{
          background: `radial-gradient(ellipse at center, transparent 0%, rgba(248,250,252,0.8) 100%)`,
        }}
      />
    </div>
  );
}

// OPTION 3: Eagle Burst - Rays from corner with eagle
function FlagBackgroundEagleBurst() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* Base */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-50 to-slate-100" />

      {/* Radial burst from top-right */}
      <div
        className="absolute -top-1/2 -right-1/2 w-full h-full"
        style={{
          background: `conic-gradient(
            from 180deg at 100% 0%,
            transparent 0deg,
            rgba(185, 28, 28, 0.04) 15deg,
            transparent 30deg,
            rgba(30, 58, 138, 0.04) 45deg,
            transparent 60deg,
            rgba(185, 28, 28, 0.04) 75deg,
            transparent 90deg,
            rgba(30, 58, 138, 0.04) 105deg,
            transparent 120deg,
            rgba(185, 28, 28, 0.04) 135deg,
            transparent 150deg,
            rgba(30, 58, 138, 0.04) 165deg,
            transparent 180deg
          )`,
        }}
      />

      {/* Eagle in corner */}
      <div
        className="absolute -bottom-20 -right-20 w-[500px] h-[500px] md:w-[700px] md:h-[700px]"
        style={{
          backgroundImage: "url('/logo.jpeg')",
          backgroundSize: "contain",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
          opacity: 0.035,
          transform: "rotate(-15deg)",
        }}
      />
    </div>
  );
}

// OPTION 4: Modern Topographic/Data Lines
function FlagBackgroundTopographic() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* Base gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-white to-slate-50" />

      {/* Topographic circles */}
      <svg className="absolute inset-0 w-full h-full opacity-[0.04]" preserveAspectRatio="none">
        {[...Array(8)].map((_, i) => (
          <circle
            key={i}
            cx="70%"
            cy="60%"
            r={`${15 + i * 8}%`}
            fill="none"
            stroke="#1E3A8A"
            strokeWidth="1"
          />
        ))}
        {[...Array(6)].map((_, i) => (
          <circle
            key={`r-${i}`}
            cx="20%"
            cy="30%"
            r={`${10 + i * 6}%`}
            fill="none"
            stroke="#B91C1C"
            strokeWidth="1"
          />
        ))}
      </svg>

      {/* Subtle eagle watermark */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px]"
        style={{
          backgroundImage: "url('/logo.jpeg')",
          backgroundSize: "contain",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
          opacity: 0.025,
        }}
      />
    </div>
  );
}

// OPTION 5: Gradient Mesh with Eagle
function FlagBackgroundGradientMesh() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* Base */}
      <div className="absolute inset-0 bg-white" />

      {/* Mesh blobs */}
      <div
        className="absolute -top-1/4 -left-1/4 w-1/2 h-1/2 rounded-full blur-3xl"
        style={{ background: "rgba(30, 58, 138, 0.08)" }}
      />
      <div
        className="absolute -bottom-1/4 -right-1/4 w-1/2 h-1/2 rounded-full blur-3xl"
        style={{ background: "rgba(185, 28, 28, 0.08)" }}
      />
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1/3 h-1/3 rounded-full blur-3xl"
        style={{ background: "rgba(201, 162, 39, 0.06)" }}
      />

      {/* Centered eagle */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px]"
        style={{
          backgroundImage: "url('/logo.jpeg')",
          backgroundSize: "contain",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
          opacity: 0.03,
        }}
      />
    </div>
  );
}

// CURRENT ACTIVE BACKGROUND - Change this to try different options!
// Options: FlagBackgroundEagleWatermark, FlagBackgroundStarsStripes,
//          FlagBackgroundEagleBurst, FlagBackgroundTopographic, FlagBackgroundGradientMesh
function FlagBackground() {
  return <FlagBackgroundEagleWatermark />;
}

// ============================================================================
// Components - Mini Game Tile (for game list) - TICKET STUB STYLE
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
        "w-full text-left transition-all duration-200 relative group",
        isSelected ? "scale-[1.02]" : "hover:scale-[1.01]"
      )}
    >
      {/* Ticket container with perforated edges */}
      <div className="relative">
        {/* Left perforated edge */}
        <div className="absolute left-0 top-0 bottom-0 w-2 flex flex-col justify-around z-10">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="w-2 h-2 rounded-full"
              style={{ marginLeft: "-4px", background: isSelected ? "#e2e8f0" : "#f1f5f9" }}
            />
          ))}
        </div>

        {/* Right perforated edge */}
        <div className="absolute right-0 top-0 bottom-0 w-2 flex flex-col justify-around z-10">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="w-2 h-2 rounded-full"
              style={{ marginRight: "-4px", background: isSelected ? "#e2e8f0" : "#f1f5f9" }}
            />
          ))}
        </div>

        {/* Main ticket body */}
        <div
          className="ml-1 mr-1 rounded overflow-hidden transition-shadow duration-200"
          style={{
            background: "#faf9f6",
            border: isSelected ? "2px solid #0f2557" : "2px dashed #d4d0c8",
            boxShadow: isSelected
              ? "0 4px 12px rgba(15, 37, 87, 0.2)"
              : "0 1px 3px rgba(0,0,0,0.05)"
          }}
        >
          {/* Top strip with conference */}
          <div
            className="px-3 py-1 flex items-center justify-between"
            style={{ background: isSelected ? "#0f2557" : "#1e293b" }}
          >
            <span
              className="text-[9px] font-bold tracking-[0.2em] uppercase"
              style={{ color: "#94a3b8" }}
            >
              {game.homeTeam.conference}
            </span>
            <span
              className="text-[9px] font-bold tracking-wider"
              style={{ color: "#64748b" }}
            >
              {game.gameTime}
            </span>
          </div>

          {/* Teams section */}
          <div className="px-3 py-2">
            {/* Away Team */}
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5 min-w-0 flex-1">
                {game.awayTeam.rank && (
                  <span
                    className="text-[10px] font-bold flex-shrink-0"
                    style={{ color: "#64748b" }}
                  >
                    #{game.awayTeam.rank}
                  </span>
                )}
                <span
                  className="font-black uppercase truncate text-sm"
                  style={{
                    color: game.awayTeam.primaryColor,
                    fontFamily: "var(--font-oswald), 'Oswald', sans-serif"
                  }}
                >
                  {game.awayTeam.shortName}
                </span>
                <span className="text-[10px] text-slate-400 flex-shrink-0">
                  {game.awayTeam.record}
                </span>
              </div>
            </div>

            {/* VS divider */}
            <div className="flex items-center gap-2 my-1">
              <div className="flex-1 border-t border-dashed" style={{ borderColor: "#d4d0c8" }} />
              <span className="text-[10px] font-bold" style={{ color: "#94a3b8" }}>VS</span>
              <div className="flex-1 border-t border-dashed" style={{ borderColor: "#d4d0c8" }} />
            </div>

            {/* Home Team */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 min-w-0 flex-1">
                {game.homeTeam.rank && (
                  <span
                    className="text-[10px] font-bold flex-shrink-0"
                    style={{ color: "#64748b" }}
                  >
                    #{game.homeTeam.rank}
                  </span>
                )}
                <span
                  className="font-black uppercase truncate text-sm"
                  style={{
                    color: game.homeTeam.primaryColor,
                    fontFamily: "var(--font-oswald), 'Oswald', sans-serif"
                  }}
                >
                  {game.homeTeam.shortName}
                </span>
                <span className="text-[10px] text-slate-400 flex-shrink-0">
                  {game.homeTeam.record}
                </span>
              </div>
            </div>
          </div>

          {/* Bottom section: Lines + Chaos */}
          <div
            className="px-3 py-2 flex items-center justify-between border-t-2 border-dashed"
            style={{ borderColor: "#d4d0c8", background: "rgba(15, 37, 87, 0.03)" }}
          >
            {/* Spread & O/U boxes */}
            <div className="flex items-center gap-2">
              {game.spread && (
                <div
                  className="px-2 py-0.5 rounded text-center"
                  style={{
                    background: "#0f2557",
                    transform: "rotate(-1deg)"
                  }}
                >
                  <span
                    className="text-xs font-black text-white"
                    style={{ fontFamily: "var(--font-oswald), 'Oswald', sans-serif" }}
                  >
                    {game.spread}
                  </span>
                </div>
              )}
              {game.total && (
                <div
                  className="px-2 py-0.5 rounded text-center"
                  style={{
                    background: "#B91C1C",
                    transform: "rotate(1deg)"
                  }}
                >
                  <span
                    className="text-xs font-black text-white"
                    style={{ fontFamily: "var(--font-oswald), 'Oswald', sans-serif" }}
                  >
                    {game.total}
                  </span>
                </div>
              )}
            </div>

            {/* Chaos badge */}
            {game.chaosRating != null && (() => {
              const cc = getChaosColor(game.chaosLabel ?? "MODERATE");
              return (
                <span
                  className={cn(
                    "text-[10px] font-bold px-1.5 py-0.5 rounded border",
                    cc.bg, cc.text, cc.border
                  )}
                >
                  {game.chaosRating.toFixed(1)}
                </span>
              );
            })()}
          </div>
        </div>
      </div>
    </button>
  );
}

// ============================================================================
// Components - Team Card (detailed view)
// ============================================================================

function TeamCard({ team, isHome }: { team: TeamData; isHome: boolean }) {
  // Use secondary color or fallback to white
  const secondaryColor = team.secondaryColor || "#ffffff";
  const textColor = "#ffffff";

  return (
    <div
      className="rounded-xl border-2 overflow-hidden shadow-lg hover:shadow-xl transition-shadow"
      style={{
        background: team.primaryColor,
        borderColor: team.primaryColor
      }}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/10">
        <div className="flex items-center gap-3">
          {/* Logo circle with secondary color */}
          <div
            className="w-14 h-14 rounded-full flex items-center justify-center text-2xl shadow-sm border-2"
            style={{
              backgroundColor: secondaryColor,
              color: team.primaryColor,
              borderColor: textColor + "40",
              fontFamily: "'Segoe UI', 'Roboto', sans-serif",
              fontWeight: 900,
            }}
          >
            {team.shortName.charAt(0)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              {team.rank && (
                <span
                  className="text-base"
                  style={{ color: textColor + "cc", fontFamily: "'Segoe UI', sans-serif", fontWeight: 700 }}
                >
                  #{team.rank}
                </span>
              )}
              <span
                className="text-xl truncate"
                style={{ color: textColor, fontFamily: "'Segoe UI', 'Roboto', sans-serif", fontWeight: 800, letterSpacing: "-0.02em" }}
              >
                {team.name}
              </span>
            </div>
            <div
              className="flex items-center gap-2"
              style={{ color: textColor + "cc", fontFamily: "'Segoe UI', sans-serif", fontWeight: 500 }}
            >
              <span>{team.conference}</span>
              <span style={{ opacity: 0.5 }}>•</span>
              <span
                className="text-xs px-2 py-0 rounded border"
                style={{
                  backgroundColor: textColor + "20",
                  color: textColor,
                  borderColor: textColor + "40"
                }}
              >
                {isHome ? "HOME" : "AWAY"}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Records Row - Horizontal pills with secondary color border */}
        <div className="flex gap-2">
          {[
            { value: team.record, label: "Record" },
            { value: team.confRecord, label: "Conf" },
            { value: team.atsRecord, label: "ATS" },
            { value: team.ouRecord, label: "O/U" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="flex-1 rounded-lg px-3 py-2 text-center"
              style={{ backgroundColor: "rgba(255,255,255,0.2)", border: `2px solid ${textColor}40` }}
            >
              <div className="text-xl" style={{ color: textColor, fontFamily: "'Segoe UI', sans-serif", fontWeight: 800 }}>{stat.value}</div>
              <div className="uppercase text-xs" style={{ color: textColor + "cc", fontFamily: "'Segoe UI', sans-serif", fontWeight: 600, letterSpacing: "0.05em" }}>{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Last 5 Games */}
        <div>
          <div
            className="text-xs uppercase tracking-wide mb-2 font-semibold"
            style={{ color: textColor + "cc" }}
          >
            Last 5 Games
          </div>
          <div className="space-y-2">
            {team.last5Games.map((game, i) => (
              <div
                key={i}
                className="rounded-lg p-2.5 transition-colors"
                style={{ backgroundColor: "rgba(255,255,255,0.15)" }}
              >
                {/* Line 1: Date, Home/Away indicator, Opponent, Result, Score */}
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-medium w-10" style={{ color: textColor + "99" }}>{game.date}</span>
                    <span className="text-xs font-medium w-4" style={{ color: textColor + "99" }}>
                      {game.isHome ? "vs" : "@"}
                    </span>
                    <span className="text-sm font-medium truncate max-w-[100px]" style={{ color: textColor }}>
                      {game.opponent}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className="text-sm font-bold"
                      style={{ color: game.result === "W" ? "#4ade80" : "#f87171" }}
                    >
                      {game.result}
                    </span>
                    <span className="text-sm font-medium" style={{ color: textColor }}>{game.score}</span>
                  </div>
                </div>
                {/* Line 2: Spread line + ATS result, O/U line + margin */}
                <div className="flex items-center gap-2 flex-wrap">
                  {/* ATS Badge with spread */}
                  <div
                    className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded"
                    style={{
                      backgroundColor: game.spreadResult > 0 ? "rgba(74, 222, 128, 0.2)" : game.spreadResult < 0 ? "rgba(248, 113, 113, 0.2)" : "rgba(255,255,255,0.2)",
                      color: game.spreadResult > 0 ? "#4ade80" : game.spreadResult < 0 ? "#f87171" : textColor
                    }}
                  >
                    <span
                      className="w-3.5 h-3.5 rounded-full flex items-center justify-center text-[10px] font-bold"
                      style={{
                        backgroundColor: game.spreadResult > 0 ? "#22c55e" : game.spreadResult < 0 ? "#ef4444" : "#94a3b8",
                        color: "#ffffff"
                      }}
                    >
                      {game.spreadResult > 0 ? "W" : game.spreadResult < 0 ? "L" : "P"}
                    </span>
                    <span>
                      {game.spread != null && (
                        <span style={{ color: textColor + "99", marginRight: "4px" }}>
                          ({game.spread > 0 ? "+" : ""}{game.spread})
                        </span>
                      )}
                      {game.spreadResult > 0 ? "+" : ""}{game.spreadResult.toFixed(1)}
                    </span>
                  </div>
                  {/* O/U Badge with line and margin */}
                  {game.ouResult && (
                    <div
                      className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded"
                      style={{
                        backgroundColor: game.ouResult === "O" ? "rgba(74, 222, 128, 0.2)" : game.ouResult === "U" ? "rgba(248, 113, 113, 0.2)" : "rgba(255,255,255,0.2)",
                        color: game.ouResult === "O" ? "#4ade80" : game.ouResult === "U" ? "#f87171" : textColor
                      }}
                    >
                      <span
                        className="w-3.5 h-3.5 rounded-full flex items-center justify-center text-[10px] font-bold"
                        style={{
                          backgroundColor: game.ouResult === "O" ? "#22c55e" : game.ouResult === "U" ? "#ef4444" : "#94a3b8",
                          color: "#ffffff"
                        }}
                      >
                        {game.ouResult}
                      </span>
                      <span>
                        {game.total != null && (
                          <span style={{ color: textColor + "99", marginRight: "4px" }}>
                            ({game.total})
                          </span>
                        )}
                        {game.totalMargin != null && (
                          <span>
                            {game.totalMargin > 0 ? "+" : ""}{game.totalMargin.toFixed(1)}
                          </span>
                        )}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {team.last5Games.length === 0 && (
              <div className="text-sm text-center py-3" style={{ color: textColor + "99" }}>No recent games</div>
            )}
          </div>
        </div>

        {/* Individual KDE Distribution Graphs */}
        {team.spreadDistribution && team.spreadDistribution.margins.length >= 5 && (
          <div className="pt-3 border-t border-white/10 space-y-3">
            <KDEGraph
              margins={team.spreadDistribution.margins}
              mean={team.spreadDistribution.mean}
              std={team.spreadDistribution.std}
              predictability={team.spreadDistribution.predictability}
              color={team.primaryColor}
              label="Spread Distribution"
            />
            {team.totalDistribution && team.totalDistribution.margins.length >= 5 && (
              <KDEGraph
                margins={team.totalDistribution.margins}
                mean={team.totalDistribution.mean}
                std={team.totalDistribution.std}
                predictability={team.totalDistribution.predictability}
                color={team.primaryColor}
                label="O/U Distribution"
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Components - Game Detail Dashboard
// ============================================================================

function GameDetailDashboard({ game, currentDate }: { game: CBBGame; currentDate: string }) {
  return (
    <div className="space-y-4">
      {/* ===== TICKET STUB HEADER (WINNER) ===== */}
      <div className="relative">
        {/* Perforated edge effect - left */}
        <div className="absolute left-0 top-0 bottom-0 w-4 flex flex-col justify-around z-10">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="w-4 h-4 rounded-full bg-slate-100" style={{ marginLeft: "-8px" }} />
          ))}
        </div>
        {/* Perforated edge effect - right */}
        <div className="absolute right-0 top-0 bottom-0 w-4 flex flex-col justify-around z-10">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="w-4 h-4 rounded-full bg-slate-100" style={{ marginRight: "-8px" }} />
          ))}
        </div>

        <div
          className="relative ml-2 mr-2 rounded-lg overflow-hidden"
          style={{
            background: "#faf9f6",
            border: "2px dashed #d4d0c8"
          }}
        >
          {/* Header strip */}
          <div className="px-6 py-3 text-center" style={{ background: "#0f2557" }}>
            <span className="text-xs font-bold tracking-[0.4em] uppercase" style={{ color: "#94a3b8" }}>
              Admit One • College Basketball
            </span>
          </div>

          <div className="p-6">
            {/* Teams */}
            <div className="flex items-center justify-center gap-8 mb-6">
              <div className="text-right">
                {game.awayTeam.rank && (
                  <span className="text-xs font-semibold" style={{ color: "#64748b" }}>#{game.awayTeam.rank}</span>
                )}
                <div
                  className="text-2xl font-black uppercase"
                  style={{
                    color: game.awayTeam.primaryColor,
                    fontFamily: "var(--font-oswald), 'Oswald', sans-serif"
                  }}
                >
                  {game.awayTeam.shortName}
                </div>
                <div className="text-xs font-semibold mt-0.5" style={{ color: "#64748b" }}>
                  {game.awayTeam.name}
                </div>
              </div>

              <div className="text-3xl font-black" style={{ color: "#0f2557" }}>
                VS
              </div>

              <div className="text-left">
                {game.homeTeam.rank && (
                  <span className="text-xs font-semibold" style={{ color: "#64748b" }}>#{game.homeTeam.rank}</span>
                )}
                <div
                  className="text-2xl font-black uppercase"
                  style={{
                    color: game.homeTeam.primaryColor,
                    fontFamily: "var(--font-oswald), 'Oswald', sans-serif"
                  }}
                >
                  {game.homeTeam.shortName}
                </div>
                <div className="text-xs font-semibold mt-0.5" style={{ color: "#64748b" }}>
                  {game.homeTeam.name}
                </div>
              </div>
            </div>

            {/* Betting lines - styled like ticket price */}
            <div className="flex justify-center gap-4 mb-6">
              {game.spread && (
                <div
                  className="px-6 py-3 rounded-lg text-center"
                  style={{
                    background: "#0f2557",
                    transform: "rotate(-1deg)"
                  }}
                >
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Line</div>
                  <div
                    className="text-3xl font-black text-white"
                    style={{ fontFamily: "var(--font-oswald), 'Oswald', sans-serif" }}
                  >
                    {game.spread}
                  </div>
                </div>
              )}
              {game.total && (
                <div
                  className="px-6 py-3 rounded-lg text-center"
                  style={{
                    background: "#B91C1C",
                    transform: "rotate(1deg)"
                  }}
                >
                  <div className="text-[10px] text-red-200 uppercase tracking-wider mb-1">Total</div>
                  <div
                    className="text-3xl font-black text-white"
                    style={{ fontFamily: "var(--font-oswald), 'Oswald', sans-serif" }}
                  >
                    {game.total}
                  </div>
                </div>
              )}
            </div>

            {/* Venue and time */}
            <div
              className="flex items-center justify-between pt-4 border-t-2 border-dashed"
              style={{ borderColor: "#d4d0c8" }}
            >
              <div className="text-sm" style={{ color: "#64748b" }}>
                <div className="font-semibold">{game.venue}</div>
                <div>{game.location}</div>
              </div>
              <div className="text-right text-sm" style={{ color: "#64748b" }}>
                <div className="font-semibold">{game.gameDate}</div>
                <div>{game.gameTime}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* ===== END TICKET STUB HEADER ===== */}

      {/* ===== TICKET STUB HEADER (FAVORITE - backup) =====
      <div className="relative">
        <div className="absolute left-0 top-0 bottom-0 w-4 flex flex-col justify-around z-10">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="w-4 h-4 rounded-full bg-slate-100" style={{ marginLeft: "-8px" }} />
          ))}
        </div>
        <div className="absolute right-0 top-0 bottom-0 w-4 flex flex-col justify-around z-10">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="w-4 h-4 rounded-full bg-slate-100" style={{ marginRight: "-8px" }} />
          ))}
        </div>
        <div className="relative ml-2 mr-2 rounded-lg overflow-hidden" style={{ background: "#faf9f6", border: "2px dashed #d4d0c8" }}>
          <div className="px-6 py-3 text-center" style={{ background: "#0f2557" }}>
            <span className="text-xs font-bold tracking-[0.4em] uppercase" style={{ color: "#94a3b8" }}>Admit One • College Basketball</span>
          </div>
          <div className="p-6">
            <div className="flex items-center justify-center gap-6 mb-6">
              <div className="text-right">
                {game.awayTeam.rank && <span className="text-xs font-semibold" style={{ color: "#64748b" }}>#{game.awayTeam.rank}</span>}
                <div className="text-2xl font-black uppercase" style={{ color: game.awayTeam.primaryColor, fontFamily: "var(--font-oswald), sans-serif" }}>{game.awayTeam.shortName}</div>
              </div>
              <div className="text-3xl font-black" style={{ color: "#0f2557" }}>VS</div>
              <div className="text-left">
                {game.homeTeam.rank && <span className="text-xs font-semibold" style={{ color: "#64748b" }}>#{game.homeTeam.rank}</span>}
                <div className="text-2xl font-black uppercase" style={{ color: game.homeTeam.primaryColor, fontFamily: "var(--font-oswald), sans-serif" }}>{game.homeTeam.shortName}</div>
              </div>
            </div>
            <div className="flex justify-center gap-4 mb-6">
              {game.spread && <div className="px-6 py-3 rounded-lg text-center" style={{ background: "#0f2557", transform: "rotate(-1deg)" }}>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Line</div>
                <div className="text-3xl font-black text-white" style={{ fontFamily: "var(--font-oswald), sans-serif" }}>{game.spread}</div>
              </div>}
              {game.total && <div className="px-6 py-3 rounded-lg text-center" style={{ background: "#B91C1C", transform: "rotate(1deg)" }}>
                <div className="text-[10px] text-red-200 uppercase tracking-wider mb-1">Total</div>
                <div className="text-3xl font-black text-white" style={{ fontFamily: "var(--font-oswald), sans-serif" }}>{game.total}</div>
              </div>}
            </div>
            <div className="flex items-center justify-between pt-4 border-t-2 border-dashed" style={{ borderColor: "#d4d0c8" }}>
              <div className="text-sm" style={{ color: "#64748b" }}><div className="font-semibold">{game.venue}</div><div>{game.location}</div></div>
              <div className="text-right text-sm" style={{ color: "#64748b" }}><div className="font-semibold">{game.gameDate}</div><div>{game.gameTime}</div></div>
            </div>
          </div>
        </div>
      </div>
      ===== END TICKET STUB HEADER (FAVORITE - backup) ===== */}

      {/* ===== SCOREBOARD HEADER (backup) =====
      <div
        className="relative rounded-2xl overflow-hidden"
        style={{
          background: "linear-gradient(180deg, #0A1628 0%, #152238 100%)",
          boxShadow: "0 4px 30px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)"
        }}
      >
        <div className="h-1 flex">
          <div className="flex-1" style={{ background: game.awayTeam.primaryColor }} />
          <div className="flex-1" style={{ background: game.homeTeam.primaryColor }} />
        </div>
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-xl flex items-center justify-center text-xl font-black"
                style={{ background: game.awayTeam.primaryColor, color: "#fff", fontFamily: "var(--font-oswald), sans-serif" }}>
                {game.awayTeam.shortName.substring(0, 3).toUpperCase()}
              </div>
              <div>
                {game.awayTeam.rank && <span className="text-xs font-bold text-slate-400">#{game.awayTeam.rank}</span>}
                <div className="text-xl font-bold text-white">{game.awayTeam.name}</div>
                <div className="text-xs text-slate-500">{game.awayTeam.conference}</div>
              </div>
            </div>
            <div className="flex flex-col items-center gap-3">
              <span className="text-2xl font-black text-slate-600">@</span>
              <div className="flex gap-3">
                {game.spread && <div className="px-5 py-3 rounded-lg text-center" style={{ background: "rgba(255,255,255,0.1)" }}>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">Spread</div>
                  <div className="text-2xl font-black text-white">{game.spread}</div>
                </div>}
                {game.total && <div className="px-5 py-3 rounded-lg text-center" style={{ background: "rgba(255,255,255,0.1)" }}>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">Total</div>
                  <div className="text-2xl font-black text-white">{game.total}</div>
                </div>}
              </div>
            </div>
            <div className="flex items-center gap-4 flex-row-reverse">
              <div className="w-16 h-16 rounded-xl flex items-center justify-center text-xl font-black"
                style={{ background: game.homeTeam.primaryColor, color: "#fff", fontFamily: "var(--font-oswald), sans-serif" }}>
                {game.homeTeam.shortName.substring(0, 3).toUpperCase()}
              </div>
              <div className="text-right">
                {game.homeTeam.rank && <span className="text-xs font-bold text-slate-400">#{game.homeTeam.rank}</span>}
                <div className="text-xl font-bold text-white">{game.homeTeam.name}</div>
                <div className="text-xs text-slate-500">{game.homeTeam.conference}</div>
              </div>
            </div>
          </div>
          <div className="flex items-center justify-between pt-4 border-t" style={{ borderColor: "rgba(255,255,255,0.1)" }}>
            <div className="flex items-center gap-4 text-sm text-slate-400">
              <span className="flex items-center gap-1.5"><MapPin className="w-4 h-4" />{game.venue}</span>
              <span className="flex items-center gap-1.5"><Clock className="w-4 h-4" />{game.gameTime}</span>
            </div>
          </div>
        </div>
      </div>
      ===== END SCOREBOARD HEADER (backup) ===== */}

      {/* OLD HEADER (backup) - uncomment to restore:
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
            <div className="flex items-center gap-2 flex-wrap justify-end">
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
          </div>
        </div>
      </div>
      */}

      {/* Spread Eagle AI Preview */}
      <SpreadEaglePreview gameId={game.id} currentDate={currentDate} />

      {/* Teams Side by Side */}
      <div className="grid md:grid-cols-2 gap-4">
        <TeamCard team={game.awayTeam} isHome={false} />
        <TeamCard team={game.homeTeam} isHome={true} />
      </div>

      {/* KDE Distribution Comparisons - Stacked */}
      {game.awayTeam.spreadDistribution && game.homeTeam.spreadDistribution && (
        <KDEComparison
          awayDist={game.awayTeam.spreadDistribution}
          homeDist={game.homeTeam.spreadDistribution}
          awayColor={game.awayTeam.primaryColor}
          homeColor={game.homeTeam.primaryColor}
          awayName={game.awayTeam.shortName}
          homeName={game.homeTeam.shortName}
          combinedScore={game.spreadPredictability}
          title="Spread Predictability"
        />
      )}

      {game.awayTeam.totalDistribution && game.homeTeam.totalDistribution && (
        <KDEComparison
          awayDist={game.awayTeam.totalDistribution}
          homeDist={game.homeTeam.totalDistribution}
          awayColor={game.awayTeam.primaryColor}
          homeColor={game.homeTeam.primaryColor}
          awayName={game.awayTeam.shortName}
          homeName={game.homeTeam.shortName}
          combinedScore={game.totalPredictability}
          title="O/U Predictability"
        />
      )}
    </div>
  );
}

// ============================================================================
// Main Page
// ============================================================================

export default function CBBDashboard() {
  const [currentDate, setCurrentDate] = useState(() => new Date());
  const [games, setGames] = useState<CBBGame[]>([]);
  const [selectedGameId, setSelectedGameId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedConferences, setSelectedConferences] = useState<Set<string>>(new Set());
  const [chaosFilter, setChaosFilter] = useState<"all" | "low" | "teaser">("all");

  // Derive unique conferences from loaded games, sorted alphabetically
  const conferences = useMemo(() => {
    const confSet = new Set<string>();
    games.forEach((g) => {
      confSet.add(g.homeTeam.conference);
      confSet.add(g.awayTeam.conference);
    });
    return Array.from(confSet).sort();
  }, [games]);

  // Filter games: conference filter + chaos/teaser filter
  const filteredGames = useMemo(() => {
    let filtered = games;
    if (selectedConferences.size > 0) {
      filtered = filtered.filter(
        (g) =>
          selectedConferences.has(g.homeTeam.conference) ||
          selectedConferences.has(g.awayTeam.conference)
      );
    }
    if (chaosFilter === "low") {
      filtered = filtered.filter((g) => g.chaosRating != null && g.chaosRating <= 2);
    } else if (chaosFilter === "teaser") {
      filtered = filtered.filter((g) => g.teaserUnder10Prob != null && g.teaserUnder10Prob >= 0.85);
    }
    return filtered;
  }, [games, selectedConferences, chaosFilter]);

  const toggleConference = (conf: string) => {
    setSelectedConferences((prev) => {
      const next = new Set(prev);
      if (next.has(conf)) {
        next.delete(conf);
      } else {
        next.add(conf);
      }
      return next;
    });
  };

  const clearConferenceFilter = () => {
    setSelectedConferences(new Set());
  };

  // Fetch games when date changes
  useEffect(() => {
    async function loadGames() {
      setIsLoading(true);
      setError(null);
      try {
        const dateStr = formatDateForAPI(currentDate);
        const fetchedGames = await fetchDashboardGames(dateStr);
        setGames(fetchedGames);
        setSelectedConferences(new Set());
        setChaosFilter("all");
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

  // Auto-select first filtered game when filter changes and current selection is hidden
  useEffect(() => {
    if (filteredGames.length > 0 && !filteredGames.find((g) => g.id === selectedGameId)) {
      setSelectedGameId(filteredGames[0].id);
    } else if (filteredGames.length === 0 && (selectedConferences.size > 0 || chaosFilter !== "all")) {
      setSelectedGameId(null);
    }
  }, [filteredGames, selectedGameId, selectedConferences, chaosFilter]);

  const selectedGame = useMemo(() => {
    return filteredGames.find((g) => g.id === selectedGameId) ?? null;
  }, [filteredGames, selectedGameId]);

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
    <div className="relative min-h-screen">
      {/* ========== PATRIOTIC HEADER ========== */}
      <header className="relative overflow-hidden" style={{ background: "linear-gradient(135deg, #0A1628 0%, #0d2137 50%, #0A1628 100%)" }}>
        {/* Animated stars background */}
        <div className="absolute inset-0 overflow-hidden">
          {/* Star field */}
          <div className="absolute top-0 left-0 w-1/3 h-full" style={{ background: "linear-gradient(180deg, #0A1628 0%, #1E3A8A 100%)" }}>
            {[...Array(20)].map((_, i) => (
              <div
                key={i}
                className="absolute w-1 h-1 bg-white rounded-full animate-pulse"
                style={{
                  top: `${Math.random() * 100}%`,
                  left: `${Math.random() * 100}%`,
                  opacity: 0.3 + Math.random() * 0.5,
                  animationDelay: `${Math.random() * 2}s`,
                  animationDuration: `${1.5 + Math.random() * 2}s`
                }}
              />
            ))}
          </div>

          {/* Diagonal stripes */}
          <div className="absolute inset-0" style={{
            background: `repeating-linear-gradient(
              -45deg,
              transparent,
              transparent 40px,
              rgba(185, 28, 28, 0.08) 40px,
              rgba(185, 28, 28, 0.08) 80px
            )`
          }} />

          {/* Red accent glow */}
          <div className="absolute top-0 right-0 w-1/2 h-full" style={{
            background: "radial-gradient(ellipse at top right, rgba(185, 28, 28, 0.3) 0%, transparent 60%)"
          }} />

          {/* Subtle accent line */}
          <div className="absolute bottom-0 left-0 right-0 h-0.5" style={{
            background: "linear-gradient(90deg, #334155 0%, #64748b 50%, #334155 100%)"
          }} />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-4 md:px-6 py-4 md:py-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            {/* Logo + Title */}
            <div className="flex items-center gap-3 md:gap-5">
              {/* Logo - no glow, cleaner */}
              <img
                src="/logo.jpeg"
                alt="Spread Eagle"
                className="w-16 h-16 md:w-24 md:h-24 lg:w-28 lg:h-28 rounded-xl md:rounded-2xl shadow-lg"
              />

              {/* Title block */}
              <div>
                <h1
                  className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-black uppercase tracking-wide"
                  style={{
                    fontFamily: "var(--font-oswald), 'Oswald', 'Impact', sans-serif",
                    color: "#0f2557",
                    letterSpacing: "0.05em",
                    lineHeight: 1
                  }}
                >
                  SPREAD EAGLE
                </h1>
                <div className="flex flex-wrap items-center gap-2 md:gap-3 mt-1 md:mt-2">
                  <span className="text-[10px] md:text-xs font-bold tracking-[0.2em] md:tracking-[0.3em] uppercase" style={{ color: "#94a3b8" }}>
                    Probability-First Analytics
                  </span>
                  <span className="hidden sm:block w-1.5 h-1.5 md:w-2 md:h-2 rounded-full" style={{ background: "#64748b" }} />
                  <span className="hidden sm:block text-[10px] md:text-xs font-bold tracking-[0.2em] uppercase" style={{ color: "#64748b" }}>
                    College Basketball
                  </span>
                </div>
              </div>
            </div>

            {/* Date Controls - dark blue grey theme */}
            <div className="flex items-center gap-1 self-end md:self-auto">
              <button
                onClick={handlePrevDay}
                className="w-10 h-10 md:w-12 md:h-12 rounded-lg md:rounded-xl flex items-center justify-center transition-all hover:scale-105 active:scale-95"
                style={{
                  background: "rgba(51, 65, 85, 0.5)",
                  border: "1px solid rgba(100, 116, 139, 0.4)",
                  backdropFilter: "blur(10px)"
                }}
              >
                <ChevronLeft className="w-4 h-4 md:w-5 md:h-5 text-slate-300" />
              </button>

              <div
                className="px-3 md:px-6 py-2 md:py-3 rounded-lg md:rounded-xl flex items-center gap-2 md:gap-3"
                style={{
                  background: "rgba(51, 65, 85, 0.6)",
                  border: "1px solid rgba(100, 116, 139, 0.5)"
                }}
              >
                <Calendar className="w-4 h-4 md:w-5 md:h-5 text-slate-400" />
                <span className="text-sm md:text-lg font-bold text-white" style={{ fontFamily: "var(--font-oswald), sans-serif" }}>
                  {formatDateForDisplay(currentDate)}
                </span>
              </div>

              <button
                onClick={handleNextDay}
                className="w-10 h-10 md:w-12 md:h-12 rounded-lg md:rounded-xl flex items-center justify-center transition-all hover:scale-105 active:scale-95"
                style={{
                  background: "rgba(51, 65, 85, 0.5)",
                  border: "1px solid rgba(100, 116, 139, 0.4)",
                  backdropFilter: "blur(10px)"
                }}
              >
                <ChevronRight className="w-4 h-4 md:w-5 md:h-5 text-white" />
              </button>
            </div>
          </div>
        </div>

        {/* Bottom red stripe accent */}
        <div className="absolute bottom-0 left-0 right-0 h-1.5 flex">
          <div className="flex-1" style={{ background: "#B91C1C" }} />
          <div className="flex-1" style={{ background: "#ffffff" }} />
          <div className="flex-1" style={{ background: "#1E3A8A" }} />
        </div>
      </header>

      <FlagBackground />

      <div className="relative z-10 mx-auto max-w-7xl px-4 py-6">

        {/* Conference Filter */}
        {!isLoading && !error && games.length > 0 && (
          <div className="mb-5">
            <div className="flex items-center gap-2 flex-wrap">
              <button
                onClick={clearConferenceFilter}
                className={cn(
                  "px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 border",
                  selectedConferences.size === 0
                    ? "bg-slate-800 text-white border-slate-800 shadow-md"
                    : "bg-white/70 text-slate-600 border-slate-200 hover:bg-white hover:border-slate-300"
                )}
              >
                All Games
              </button>
              {conferences.map((conf) => {
                const isActive = selectedConferences.has(conf);
                const gameCount = games.filter(
                  (g) => g.homeTeam.conference === conf || g.awayTeam.conference === conf
                ).length;
                return (
                  <button
                    key={conf}
                    onClick={() => toggleConference(conf)}
                    className={cn(
                      "px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 border",
                      isActive
                        ? "bg-slate-800 text-white border-slate-800 shadow-md"
                        : "bg-white/70 text-slate-600 border-slate-200 hover:bg-white hover:border-slate-300"
                    )}
                  >
                    {conf}
                    <span
                      className={cn(
                        "ml-1.5 text-xs",
                        isActive ? "text-slate-300" : "text-slate-400"
                      )}
                    >
                      {gameCount}
                    </span>
                  </button>
                );
              })}

              {/* Chaos / Teaser filters */}
              <div className="w-px h-6 bg-slate-300 mx-1" />
              <button
                onClick={() => setChaosFilter(chaosFilter === "low" ? "all" : "low")}
                className={cn(
                  "px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 border",
                  chaosFilter === "low"
                    ? "bg-emerald-600 text-white border-emerald-600 shadow-md"
                    : "bg-white/70 text-slate-600 border-slate-200 hover:bg-white hover:border-slate-300"
                )}
              >
                Low Chaos
              </button>
              <button
                onClick={() => setChaosFilter(chaosFilter === "teaser" ? "all" : "teaser")}
                className={cn(
                  "px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 border",
                  chaosFilter === "teaser"
                    ? "bg-amber-600 text-white border-amber-600 shadow-md"
                    : "bg-white/70 text-slate-600 border-slate-200 hover:bg-white hover:border-slate-300"
                )}
              >
                Teaser Friendly
              </button>
            </div>
          </div>
        )}

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
          <div className="grid lg:grid-cols-[400px_1fr] gap-6">
            {/* Game List */}
            <div className="space-y-3 max-h-[calc(100vh-200px)] overflow-y-auto pr-2">
              <div className="text-sm font-semibold text-slate-600 uppercase tracking-wide px-1">
                {selectedConferences.size > 0
                  ? `Games (${filteredGames.length} of ${games.length})`
                  : `Games (${games.length})`}
              </div>
              {filteredGames.length === 0 && selectedConferences.size > 0 && (
                <div className="text-center py-8 text-sm text-slate-500">
                  No games for selected conferences
                </div>
              )}
              {filteredGames.map((game) => (
                <MiniGameTile
                  key={game.id}
                  game={game}
                  isSelected={game.id === selectedGameId}
                  onClick={() => setSelectedGameId(game.id)}
                />
              ))}
            </div>

            {/* Selected Game Detail */}
            {selectedGame && <GameDetailDashboard game={selectedGame} currentDate={formatDateForAPI(currentDate)} />}
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-slate-500 font-medium tracking-wide uppercase">
          Spread Eagle • Probability-First Sports Analytics • Not Financial Advice
        </div>
      </div>

      {/* Patriotic bottom accent bar */}
      <div className="h-1.5 flex relative z-20">
        <div className="flex-1" style={{ background: "#1E3A8A" }} />
        <div className="flex-1" style={{ background: "#ffffff" }} />
        <div className="flex-1" style={{ background: "#B91C1C" }} />
      </div>
    </div>
  );
}
