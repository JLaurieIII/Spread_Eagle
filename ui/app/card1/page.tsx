"use client";

import GameCard1, { demoGameData } from "@/components/GameCard1";

/**
 * Demo page for Card 1 - Game Context + Betting Snapshot
 */
export default function Card1DemoPage() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-8">
      <div className="w-full max-w-4xl">
        <GameCard1 {...demoGameData} />
      </div>
    </div>
  );
}
