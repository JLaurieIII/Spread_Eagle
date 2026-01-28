"use client";

import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import Image from "next/image";

// ============================================================================
// Rotating Quotes
// ============================================================================

const BALDY_QUOTES = [
  "That line is begging you to get emotional. Don't.",
  "If you don't rebound, you don't deserve happiness.",
  "I don't hate the pick. I hate that I like it.",
  "Tempo tells the truth. The rest is noise.",
  "Vegas sets the center. We hunt the shape.",
  "From my perch, this line looks like dead money.",
  "I've been circling this matchup all week.",
  "Sharp money doesn't panic. Neither do eagles.",
];

function useRotatingQuote() {
  const [index, setIndex] = useState(0);
  const [fade, setFade] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setFade(false);
      setTimeout(() => {
        setIndex((i) => (i + 1) % BALDY_QUOTES.length);
        setFade(true);
      }, 400);
    }, 4500);
    return () => clearInterval(interval);
  }, []);

  return { quote: BALDY_QUOTES[index], fade };
}

// ============================================================================
// Scroll reveal hook
// ============================================================================

function useReveal() {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          obs.disconnect();
        }
      },
      { threshold: 0.15 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return { ref, visible };
}

function RevealSection({
  children,
  className = "",
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const { ref, visible } = useReveal();
  return (
    <div
      ref={ref}
      className={`transition-all duration-700 ${
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
      } ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
}

// ============================================================================
// Quick Fact Card
// ============================================================================

function FactCard({
  label,
  value,
  delay,
}: {
  label: string;
  value: string;
  delay: number;
}) {
  const { ref, visible } = useReveal();
  return (
    <div
      ref={ref}
      className={`relative overflow-hidden rounded-xl border border-red-900/30 bg-gradient-to-br from-slate-800/80 to-slate-900/90 p-5 transition-all duration-500 hover:scale-[1.03] hover:border-red-700/50 ${
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
      }`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      <div className="absolute top-0 left-0 h-1 w-full bg-gradient-to-r from-red-600 via-white/60 to-blue-700" />
      <div className="text-xs font-bold uppercase tracking-widest text-red-400 mb-1.5">
        {label}
      </div>
      <div className="text-base text-slate-200 leading-relaxed">{value}</div>
    </div>
  );
}

// ============================================================================
// Delivery Item
// ============================================================================

function DeliveryItem({
  title,
  desc,
  icon,
}: {
  title: string;
  desc: string;
  icon: string;
}) {
  return (
    <div className="flex gap-4 items-start group">
      <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-red-600/20 border border-red-700/30 flex items-center justify-center text-lg group-hover:bg-red-600/30 transition-colors">
        {icon}
      </div>
      <div>
        <div className="font-bold text-white text-sm mb-0.5">{title}</div>
        <div className="text-slate-400 text-sm leading-relaxed">{desc}</div>
      </div>
    </div>
  );
}

// ============================================================================
// Step Card
// ============================================================================

function StepCard({
  num,
  text,
  delay,
}: {
  num: number;
  text: string;
  delay: number;
}) {
  const { ref, visible } = useReveal();
  return (
    <div
      ref={ref}
      className={`flex items-start gap-4 transition-all duration-500 ${
        visible ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-6"
      }`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-red-600 to-red-800 flex items-center justify-center text-white font-black text-sm shadow-lg shadow-red-900/40">
        {num}
      </div>
      <p className="text-slate-300 text-base leading-relaxed pt-1.5">{text}</p>
    </div>
  );
}

// ============================================================================
// Main Page
// ============================================================================

export default function MeetBaldyPage() {
  const { quote, fade } = useRotatingQuote();
  const [email, setEmail] = useState("");
  const [heroLoaded, setHeroLoaded] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setHeroLoaded(true), 100);
    return () => clearTimeout(t);
  }, []);

  return (
    <>
      {/* SEO head via Next.js metadata is in layout; we set document title client-side as fallback */}
      <div className="min-h-screen bg-[#0a0f1a] text-white selection:bg-red-600/40 selection:text-white">
        {/* ── Noise texture overlay ────────────────────────────── */}
        <div
          className="pointer-events-none fixed inset-0 z-50 opacity-[0.03]"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
          }}
        />

        {/* ════════════════════════════════════════════════════════
            HERO
        ════════════════════════════════════════════════════════ */}
        <section className="relative overflow-hidden min-h-[100dvh] flex items-center">
          {/* Background atmosphere */}
          <div className="absolute inset-0">
            <div className="absolute inset-0 bg-gradient-to-br from-[#0a1628] via-[#111827] to-[#1a0a0a]" />
            <div className="absolute top-0 right-0 w-[60%] h-[60%] bg-red-900/10 rounded-full blur-[120px]" />
            <div className="absolute bottom-0 left-0 w-[40%] h-[40%] bg-blue-900/15 rounded-full blur-[100px]" />
            {/* Diagonal stripe accent */}
            <div
              className="absolute inset-0 opacity-[0.04]"
              style={{
                backgroundImage:
                  "repeating-linear-gradient(135deg, transparent, transparent 40px, rgba(255,255,255,0.1) 40px, rgba(255,255,255,0.1) 41px)",
              }}
            />
          </div>

          <div className="relative z-10 w-full max-w-7xl mx-auto px-6 py-16 lg:py-0">
            <div className="grid lg:grid-cols-2 gap-12 lg:gap-8 items-center">
              {/* Left — Copy */}
              <div
                className={`order-2 lg:order-1 transition-all duration-1000 ${
                  heroLoaded
                    ? "opacity-100 translate-y-0"
                    : "opacity-0 translate-y-10"
                }`}
              >
                {/* Eyebrow */}
                <div className="flex items-center gap-2 mb-6">
                  <div className="h-px w-8 bg-red-500" />
                  <span className="text-xs font-bold uppercase tracking-[0.25em] text-red-400">
                    Spread Eagle
                  </span>
                </div>

                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black leading-[1.05] mb-6">
                  Meet{" "}
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-500 via-red-400 to-red-600">
                    Baldy
                  </span>
                  <br />
                  <span className="text-slate-300 text-3xl sm:text-4xl lg:text-[2.75rem]">
                    Spread Eagle&apos;s Most Patriotic Degenerate
                  </span>
                </h1>

                <p className="text-lg text-slate-400 leading-relaxed mb-8 max-w-lg">
                  A sharp-tongued Philly bald eagle who loves America, college
                  hoops, and the occasional questionable wager — and somehow
                  still brings receipts.
                </p>

                {/* Hero bullets */}
                <div className="space-y-3 mb-10">
                  {[
                    ["🎯", "One AI preview per game per day", "cached, fast, consistent"],
                    ["📰", "Grounded in data + news", "injuries, line movement, context"],
                    ["🔥", "Punchy picks", "spread, total, moneyline — with reasons"],
                  ].map(([icon, title, sub]) => (
                    <div key={title} className="flex items-start gap-3">
                      <span className="text-lg mt-0.5">{icon}</span>
                      <div>
                        <span className="text-white font-semibold text-sm">
                          {title}
                        </span>
                        <span className="text-slate-500 text-sm"> — {sub}</span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* CTAs */}
                <div className="flex flex-wrap gap-4">
                  <Link
                    href="/"
                    className="inline-flex items-center gap-2 px-7 py-3.5 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white font-bold rounded-xl transition-all duration-200 shadow-lg shadow-red-900/40 hover:shadow-red-800/60 hover:scale-[1.02]"
                  >
                    See Today&apos;s Picks
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2.5}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M13 7l5 5m0 0l-5 5m5-5H6"
                      />
                    </svg>
                  </Link>
                  <a
                    href="#how-it-works"
                    className="inline-flex items-center gap-2 px-7 py-3.5 border border-slate-600 hover:border-slate-400 text-slate-300 hover:text-white font-semibold rounded-xl transition-all duration-200 hover:bg-white/5"
                  >
                    How it works
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </a>
                </div>
              </div>

              {/* Right — Hero Image */}
              <div
                className={`order-1 lg:order-2 flex justify-center lg:justify-end transition-all duration-1000 delay-300 ${
                  heroLoaded
                    ? "opacity-100 translate-y-0 scale-100"
                    : "opacity-0 translate-y-6 scale-95"
                }`}
              >
                <div className="relative">
                  {/* Glow behind image */}
                  <div className="absolute -inset-6 bg-gradient-to-tr from-red-600/20 via-transparent to-blue-600/15 rounded-3xl blur-2xl" />
                  <div className="relative rounded-2xl overflow-hidden border-2 border-slate-700/50 shadow-2xl shadow-black/60 max-w-[440px]">
                    <Image
                      src="/baldy.jpeg"
                      alt="Baldy the Spread Eagle — a patriotic bald eagle gambler with a Philly attitude"
                      width={440}
                      height={600}
                      priority
                      className="w-full h-auto object-cover"
                    />
                    {/* Bottom gradient fade */}
                    <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-[#0a0f1a] to-transparent" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Scroll indicator */}
          <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 animate-bounce">
            <div className="w-5 h-8 rounded-full border-2 border-slate-600 flex items-start justify-center p-1">
              <div className="w-1.5 h-2.5 bg-slate-500 rounded-full" />
            </div>
          </div>
        </section>

        {/* ════════════════════════════════════════════════════════
            WHO IS BALDY?
        ════════════════════════════════════════════════════════ */}
        <section className="relative py-24 lg:py-32">
          <div className="max-w-5xl mx-auto px-6">
            <RevealSection>
              <div className="flex items-center gap-3 mb-4">
                <div className="h-px w-10 bg-red-600" />
                <span className="text-xs font-bold uppercase tracking-[0.2em] text-red-400">
                  The Legend
                </span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-black text-white mb-6">
                Who the hell is Baldy?
              </h2>
              <p className="text-lg text-slate-400 leading-relaxed max-w-2xl mb-4">
                Baldy is the unofficial commissioner of Spread Eagle — a bald
                eagle with a Philly attitude and a suspiciously high confidence
                in mid-major unders.
              </p>
              <p className="text-lg text-slate-400 leading-relaxed max-w-2xl">
                He&apos;s not a villain. He&apos;s not a saint. He&apos;s the friend who
                shows up wearing an American-flag jacket, calls the refs
                &ldquo;bozos,&rdquo; and somehow explains tempo, turnovers, and
                free-throw rate better than half the internet.
              </p>
            </RevealSection>

            {/* Quick Facts Grid */}
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-14">
              <FactCard
                label="Species"
                value="Bald Eagle (obviously)"
                delay={0}
              />
              <FactCard
                label="Hometown"
                value="South Philly (spiritually, at least)"
                delay={100}
              />
              <FactCard
                label="Fuel"
                value="Caffeine, chaos, and the smell of a close line"
                delay={200}
              />
              <FactCard
                label="Special Skill"
                value="Turning stats into trash talk — fast"
                delay={300}
              />
            </div>
          </div>
        </section>

        {/* ════════════════════════════════════════════════════════
            BALDY'S BIO
        ════════════════════════════════════════════════════════ */}
        <section className="relative py-24 lg:py-32 overflow-hidden">
          {/* Accent stripe */}
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-red-600 via-white/40 to-blue-700" />

          <div className="max-w-5xl mx-auto px-6">
            <RevealSection>
              <div className="lg:grid lg:grid-cols-[1fr_1.2fr] gap-16 items-start">
                <div>
                  <div className="flex items-center gap-3 mb-4">
                    <div className="h-px w-10 bg-red-600" />
                    <span className="text-xs font-bold uppercase tracking-[0.2em] text-red-400">
                      The Full Story
                    </span>
                  </div>
                  <h2 className="text-3xl sm:text-4xl font-black text-white mb-2">
                    Baldy&apos;s Bio
                  </h2>
                  <p className="text-slate-500 text-sm italic mb-6">
                    No relation. Don&apos;t ask.
                  </p>
                </div>

                <div className="space-y-5 text-slate-400 text-base leading-relaxed">
                  <p>
                    Baldy &ldquo;Spread Eagle&rdquo; McGraw is a loud, lovable,
                    slightly unhinged bald eagle who lives for two things:{" "}
                    <span className="text-white font-semibold">America</span>{" "}
                    and{" "}
                    <span className="text-white font-semibold">
                      a number that makes sense
                    </span>
                    .
                  </p>
                  <p>
                    He watches college basketball like it owes him money.
                    He&apos;s allergic to soft analysis. If a team&apos;s
                    rebounding stinks or their point guard turns it over like
                    it&apos;s a hobby, Baldy&apos;s gonna tell you — loudly —
                    and then he&apos;s gonna tell you what he&apos;s doing about
                    it.
                  </p>
                  <p>
                    He&apos;s funny. He&apos;s blunt. He&apos;s occasionally
                    dramatic. But he&apos;s built on one rule:
                  </p>
                  <div className="border-l-4 border-red-600 pl-5 py-2">
                    <p className="text-xl font-black text-white">
                      No pick without a reason.
                    </p>
                  </div>
                </div>
              </div>
            </RevealSection>
          </div>
        </section>

        {/* ════════════════════════════════════════════════════════
            WHAT BALDY DELIVERS
        ════════════════════════════════════════════════════════ */}
        <section className="relative py-24 lg:py-32 bg-gradient-to-b from-transparent via-slate-900/50 to-transparent">
          <div className="max-w-5xl mx-auto px-6">
            <RevealSection>
              <div className="flex items-center gap-3 mb-4">
                <div className="h-px w-10 bg-red-600" />
                <span className="text-xs font-bold uppercase tracking-[0.2em] text-red-400">
                  The Daily Preview
                </span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-black text-white mb-4">
                What Baldy delivers every day
              </h2>
              <p className="text-slate-400 text-base mb-12 max-w-xl">
                Each game gets a single daily preview. One take. No rerolls.
                Here&apos;s what&apos;s in it.
              </p>
            </RevealSection>

            <RevealSection delay={150}>
              <div className="grid sm:grid-cols-2 gap-x-10 gap-y-7">
                <DeliveryItem
                  icon="📰"
                  title="Headline"
                  desc="Punchy, memeable, Baldy-approved"
                />
                <DeliveryItem
                  icon="⚡"
                  title="TL;DR Prediction"
                  desc="Who wins and why in 2–4 sentences"
                />
                <DeliveryItem
                  icon="🎯"
                  title="Spread Pick"
                  desc="With rationale + confidence level"
                />
                <DeliveryItem
                  icon="📊"
                  title="Total Pick"
                  desc="Over/Under lean + matchup logic"
                />
                <DeliveryItem
                  icon="🔑"
                  title="Key Factors"
                  desc="Tempo, shooting, TOs, rebounding, foul rate, rest"
                />
                <DeliveryItem
                  icon="⚠️"
                  title="Risk Notes"
                  desc="How this pick could blow up in your face"
                />
              </div>
            </RevealSection>

            <RevealSection delay={300}>
              <div className="mt-14 border-l-4 border-slate-600 pl-5 py-2">
                <p className="text-slate-400 italic text-base">
                  Baldy doesn&apos;t do &ldquo;locks.&rdquo; He does{" "}
                  <span className="text-white font-bold not-italic">
                    angles
                  </span>
                  .
                </p>
              </div>
            </RevealSection>
          </div>
        </section>

        {/* ════════════════════════════════════════════════════════
            HOW IT WORKS
        ════════════════════════════════════════════════════════ */}
        <section id="how-it-works" className="relative py-24 lg:py-32">
          <div className="max-w-5xl mx-auto px-6">
            <RevealSection>
              <div className="flex items-center gap-3 mb-4">
                <div className="h-px w-10 bg-blue-500" />
                <span className="text-xs font-bold uppercase tracking-[0.2em] text-blue-400">
                  Under the Hood
                </span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-black text-white mb-3">
                One call per game. No spam. No rerolls.
              </h2>
              <p className="text-slate-400 text-base mb-14 max-w-2xl">
                Spread Eagle generates{" "}
                <span className="text-white font-semibold">one</span> AI
                preview per game{" "}
                <span className="text-white font-semibold">per day</span> —
                then stores it in a database so your page loads instantly and
                the take stays consistent.
              </p>
            </RevealSection>

            <div className="space-y-8 max-w-xl">
              <StepCard
                num={1}
                text="Pull structured matchup data — team performance, recent form, style metrics"
                delay={0}
              />
              <StepCard
                num={2}
                text="Check fresh news — injuries, suspensions, notable updates, line movement"
                delay={100}
              />
              <StepCard
                num={3}
                text="Run one model call to write Baldy's preview in his voice"
                delay={200}
              />
              <StepCard
                num={4}
                text="Cache the result in Postgres — fast, reproducible, and cheap"
                delay={300}
              />
            </div>

            <RevealSection delay={400}>
              <div className="mt-14 p-5 rounded-xl border border-slate-700/50 bg-slate-800/40 max-w-xl">
                <p className="text-sm text-slate-500">
                  <span className="text-slate-400 font-semibold">
                    Responsible gaming:
                  </span>{" "}
                  For entertainment only. No guarantees. Bet responsibly.
                </p>
              </div>
            </RevealSection>
          </div>
        </section>

        {/* ════════════════════════════════════════════════════════
            ROTATING QUOTES
        ════════════════════════════════════════════════════════ */}
        <section className="relative py-24 lg:py-32 bg-gradient-to-b from-transparent via-red-950/10 to-transparent">
          <div className="max-w-4xl mx-auto px-6 text-center">
            <RevealSection>
              <div className="flex items-center justify-center gap-3 mb-10">
                <div className="h-px w-10 bg-red-600" />
                <span className="text-xs font-bold uppercase tracking-[0.2em] text-red-400">
                  Baldy Wisdom
                </span>
                <div className="h-px w-10 bg-red-600" />
              </div>
            </RevealSection>

            <div className="min-h-[120px] flex items-center justify-center">
              <p
                className={`text-2xl sm:text-3xl lg:text-4xl font-black text-white leading-snug max-w-2xl transition-opacity duration-400 ${
                  fade ? "opacity-100" : "opacity-0"
                }`}
              >
                &ldquo;{quote}&rdquo;
              </p>
            </div>

            <div className="mt-8 flex items-center justify-center gap-2">
              <span className="text-2xl">🦅</span>
              <span className="text-sm text-slate-500 font-semibold">
                — Baldy &ldquo;Spread Eagle&rdquo; McGraw
              </span>
            </div>
          </div>
        </section>

        {/* ════════════════════════════════════════════════════════
            NEWSLETTER CTA
        ════════════════════════════════════════════════════════ */}
        <section className="relative py-24 lg:py-32">
          <div className="max-w-2xl mx-auto px-6">
            <RevealSection>
              <div className="relative overflow-hidden rounded-2xl border border-slate-700/50 bg-gradient-to-br from-slate-800/80 to-slate-900/90 p-8 sm:p-12">
                {/* Top stripe */}
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-600 via-white/60 to-blue-700" />

                <div className="text-center mb-8">
                  <span className="text-4xl mb-4 block">🦅</span>
                  <h2 className="text-2xl sm:text-3xl font-black text-white mb-3">
                    Want Baldy in your inbox?
                  </h2>
                  <p className="text-slate-400 text-base">
                    Get the daily slate, the best angles, and the games Baldy
                    refuses to touch.
                  </p>
                </div>

                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    // placeholder — wire to email service
                  }}
                  className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto"
                >
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your@email.com"
                    required
                    className="flex-1 px-4 py-3 rounded-xl bg-slate-900/80 border border-slate-600 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-red-600/50 focus:border-red-600 text-sm"
                  />
                  <button
                    type="submit"
                    className="px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white font-bold rounded-xl transition-all duration-200 shadow-lg shadow-red-900/30 hover:shadow-red-800/50 hover:scale-[1.02] text-sm whitespace-nowrap"
                  >
                    Send the slate
                  </button>
                </form>
              </div>
            </RevealSection>
          </div>
        </section>

        {/* ════════════════════════════════════════════════════════
            STICKY CTA (mobile)
        ════════════════════════════════════════════════════════ */}
        <div className="fixed bottom-0 left-0 right-0 z-40 lg:hidden">
          <div className="bg-gradient-to-t from-[#0a0f1a] via-[#0a0f1a]/95 to-transparent pt-6 pb-4 px-4">
            <Link
              href="/"
              className="flex items-center justify-center gap-2 w-full py-3.5 bg-gradient-to-r from-red-600 to-red-700 text-white font-bold rounded-xl shadow-lg shadow-red-900/50 text-sm"
            >
              See Today&apos;s Picks
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M13 7l5 5m0 0l-5 5m5-5H6"
                />
              </svg>
            </Link>
          </div>
        </div>

        {/* ════════════════════════════════════════════════════════
            FOOTER
        ════════════════════════════════════════════════════════ */}
        <footer className="border-t border-slate-800 py-10">
          <div className="max-w-5xl mx-auto px-6 text-center">
            <div className="flex items-center justify-center gap-2 mb-4">
              <span className="text-red-500">★</span>
              <span className="text-sm font-bold text-slate-400 uppercase tracking-wider">
                Spread Eagle
              </span>
              <span className="text-blue-500">★</span>
            </div>
            <p className="text-xs text-slate-600 max-w-lg mx-auto leading-relaxed">
              <span className="text-slate-500 font-semibold">Disclaimer:</span>{" "}
              Spread Eagle content is for entertainment and informational
              purposes only and is not betting or financial advice. Outcomes are
              uncertain. Please bet responsibly.
            </p>
          </div>
        </footer>

        {/* Extra bottom padding for sticky CTA on mobile */}
        <div className="h-20 lg:hidden" />
      </div>
    </>
  );
}
