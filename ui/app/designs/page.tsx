"use client";

import React from "react";
import Link from "next/link";

/**
 * SPREAD EAGLE - DESIGN GALLERY
 *
 * A showcase of all available design variations
 */

const designs = [
  {
    id: "patriot-dark",
    name: "Patriot Dark",
    description: "Bold American patriotism meets premium dark mode. Deep navy base with metallic gold accents, dramatic shadows and glowing effects.",
    gradient: "linear-gradient(135deg, #0a1628, #1e3a8a, #B91C1C)",
    accent: "#C9A227",
  },
  {
    id: "clean-minimal",
    name: "Clean Minimal",
    description: "Swiss-inspired minimalism with surgical precision. Crisp white background, thin lines, and team colors as the only accent.",
    gradient: "linear-gradient(135deg, #ffffff, #f8fafc, #e2e8f0)",
    accent: "#1e293b",
    light: true,
  },
  {
    id: "sports-broadcast",
    name: "Sports Broadcast",
    description: "ESPN/Fox Sports broadcast energy. Bold diagonal cuts, high contrast team colors, scoreboard-style layouts with animations.",
    gradient: "linear-gradient(135deg, #0f0f0f, #1a1a2e, #B91C1C)",
    accent: "#FFD700",
  },
  {
    id: "luxury-premium",
    name: "Luxury Premium",
    description: "High-end VIP lounge aesthetic. Rich blacks with champagne gold, velvet textures, elegant serif typography, art deco patterns.",
    gradient: "linear-gradient(135deg, #0a0a0a, #1a1a1a, #0d0d0d)",
    accent: "#D4AF37",
  },
  {
    id: "neon-vegas",
    name: "Neon Vegas",
    description: "Las Vegas sportsbook neon energy. Deep purple backgrounds, neon pink and cyan accents, glowing effects and retro-futuristic grids.",
    gradient: "linear-gradient(135deg, #0a000f, #1a0029, #ff00ff20)",
    accent: "#ff00ff",
  },
  {
    id: "mobile-first",
    name: "Mobile First",
    description: "Phone-optimized with card-based navigation, large touch targets, bottom nav bar, and swipeable team comparisons.",
    gradient: "linear-gradient(135deg, #0f172a, #1e293b, #334155)",
    accent: "#22c55e",
  },
];

export default function DesignGallery() {
  return (
    <div
      className="min-h-screen"
      style={{
        background: "linear-gradient(180deg, #0a1628 0%, #0f172a 100%)",
        fontFamily: "'Inter', -apple-system, sans-serif"
      }}
    >
      {/* Header */}
      <header className="border-b border-slate-800/50">
        <div className="max-w-6xl mx-auto px-8 py-8">
          <div className="flex items-center gap-4">
            <img
              src="/logo.jpeg"
              alt="Spread Eagle"
              className="w-16 h-16 rounded-xl shadow-2xl"
            />
            <div>
              <h1
                className="text-3xl font-black tracking-tight"
                style={{
                  background: "linear-gradient(135deg, #C9A227, #FFD700, #C9A227)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent"
                }}
              >
                DESIGN GALLERY
              </h1>
              <p className="text-slate-500 text-sm">
                Explore different UI designs for Spread Eagle
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Gallery */}
      <main className="max-w-6xl mx-auto px-8 py-12">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {designs.map((design) => (
            <Link
              key={design.id}
              href={`/designs/${design.id}`}
              className="group"
            >
              <div
                className="rounded-2xl overflow-hidden transition-all duration-300 group-hover:scale-[1.02] group-hover:shadow-2xl"
                style={{
                  background: "rgba(30, 41, 59, 0.5)",
                  border: "1px solid rgba(71, 85, 105, 0.3)"
                }}
              >
                {/* Preview gradient */}
                <div
                  className="h-40 relative"
                  style={{ background: design.gradient }}
                >
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div
                      className="w-12 h-12 rounded-xl flex items-center justify-center font-black text-2xl"
                      style={{
                        background: design.accent + "30",
                        color: design.accent,
                        border: `2px solid ${design.accent}60`
                      }}
                    >
                      SE
                    </div>
                  </div>
                </div>

                {/* Info */}
                <div className="p-5">
                  <h3 className="text-lg font-bold text-white mb-2">{design.name}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{design.description}</p>

                  <div className="mt-4 flex items-center gap-2">
                    <span
                      className="text-xs font-medium px-3 py-1 rounded-full"
                      style={{
                        background: design.accent + "20",
                        color: design.accent
                      }}
                    >
                      View Design →
                    </span>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {/* Note */}
        <div className="mt-16 text-center">
          <p className="text-slate-500 text-sm">
            Each design uses the same data structure from the production dashboard.
            <br />
            Click any design to view the full interactive prototype.
          </p>
        </div>
      </main>

      {/* Back to production */}
      <footer className="border-t border-slate-800/50">
        <div className="max-w-6xl mx-auto px-8 py-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
          >
            <span>←</span>
            <span>Back to Production Dashboard</span>
          </Link>
        </div>
      </footer>
    </div>
  );
}
