"use client";

/**
 * ScoreBadge — Phase 1
 *
 * Displays the overall AI match score prominently at the top,
 * followed by all 4 score signals as labelled, colour-coded progress bars.
 *
 * QA-9: All 4 bars render when data is present.
 * QA-10: When score.client_quality is null, shows "—" gracefully. No crash.
 */

import { motion } from "framer-motion";

// ── Types ─────────────────────────────────────────────────────────────────────

interface ScoreBadgeProps {
  /** Overall match score 0–100 */
  overall_score: number;
  /** Skill match score 0–100. Null → shows "—" bar. */
  skill_match_score?: number | null;
  /** Semantic relevance / ROI score 0–100 */
  semantic_relevance_score?: number | null;
  /** Competition score 0–100 */
  competition_score?: number | null;
  /**
   * Client quality score from job.score.client_quality (0.0 – 1.0 float).
   * Multiplied by 100 for display.
   */
  client_quality?: number | null;
}

// ── Colour helpers ────────────────────────────────────────────────────────────

function scoreColour(score: number | null | undefined): {
  text: string;
  bar: string;
  border: string;
} {
  if (score == null)         return { text: "text-slate-500", bar: "bg-slate-700", border: "border-slate-700" };
  if (score >= 70)           return { text: "text-neon-lime",   bar: "bg-neon-lime",   border: "border-neon-lime" };
  if (score >= 40)           return { text: "text-neon-orange", bar: "bg-neon-orange", border: "border-neon-orange" };
  return                            { text: "text-neon-pink",   bar: "bg-neon-pink",   border: "border-neon-pink" };
}

// ── Signal bar ────────────────────────────────────────────────────────────────

interface SignalBarProps {
  label: string;
  /** 0–100 value, or null for graceful "—" fallback */
  value: number | null | undefined;
  /** Optional animation delay */
  delay?: number;
}

function SignalBar({ label, value, delay = 0 }: SignalBarProps) {
  const normalised = value == null ? null : Math.max(0, Math.min(100, value));
  const colours = scoreColour(normalised);
  const displayValue = normalised == null ? "—" : `${Math.round(normalised)}`;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-slate-400">
          {label}
        </span>
        <span className={`font-mono text-xs font-bold w-8 text-right ${colours.text}`}>
          {displayValue}
        </span>
      </div>
      <div className="h-2 bg-surface-800 border border-border overflow-hidden">
        <motion.div
          className={`h-full ${colours.bar}`}
          initial={{ width: 0 }}
          animate={{ width: normalised == null ? "0%" : `${normalised}%` }}
          transition={{ duration: 0.5, ease: "easeOut", delay }}
        />
      </div>
    </div>
  );
}

// ── ScoreBadge ────────────────────────────────────────────────────────────────

export function ScoreBadge({
  overall_score,
  skill_match_score,
  semantic_relevance_score,
  competition_score,
  client_quality,
}: ScoreBadgeProps) {
  // Normalise overall score to 0-100
  const overall = Math.max(0, Math.min(100, Math.round(overall_score)));
  const overallColours = scoreColour(overall);

  // client_quality arrives as a 0-1 float — scale to 0-100 for display
  const clientQualityPct =
    client_quality == null ? null : Math.round(client_quality * 100);

  const signals: SignalBarProps[] = [
    { label: "Skill Match",     value: skill_match_score,         delay: 0.10 },
    { label: "ROI / Relevance", value: semantic_relevance_score,  delay: 0.15 },
    { label: "Competition",     value: competition_score,          delay: 0.20 },
    { label: "Client Quality",  value: clientQualityPct,          delay: 0.25 },
  ];

  return (
    <div className="brutal-panel p-5 space-y-5">
      {/* Overall score — large, colour-coded headline number */}
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">
            Match Score
          </div>
          <div className={`text-5xl font-bold font-mono leading-none ${overallColours.text}`}>
            {overall}
          </div>
        </div>

        {/* Circular gauge hint */}
        <div
          className={`w-16 h-16 border-4 ${overallColours.border} flex items-center justify-center`}
          style={{ borderRadius: 0 }}
        >
          <motion.span
            className={`text-2xl font-bold font-mono ${overallColours.text}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            {overall >= 70 ? "A" : overall >= 40 ? "B" : "C"}
          </motion.span>
        </div>
      </div>

      {/* Divider */}
      <div className="h-px bg-border" />

      {/* 4 signal bars */}
      <div className="space-y-3">
        {signals.map((sig) => (
          <SignalBar key={sig.label} {...sig} />
        ))}
      </div>
    </div>
  );
}

export default ScoreBadge;
