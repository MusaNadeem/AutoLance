"use client";

import { motion } from "framer-motion";

interface ScoreBadgeProps {
  overall_score: number;
  skill_match_score?: number | null;
  semantic_relevance_score?: number | null;
  competition_score?: number | null;
  client_quality?: number | null;
}

function scoreColour(score: number | null | undefined): { text: string; bar: string; border: string } {
  if (score == null)    return { text: "text-slate-500",   bar: "bg-slate-700",   border: "border-slate-700" };
  if (score >= 70)      return { text: "text-neon-lime",   bar: "bg-neon-lime",   border: "border-neon-lime" };
  if (score >= 40)      return { text: "text-neon-orange", bar: "bg-neon-orange", border: "border-neon-orange" };
  return                       { text: "text-neon-pink",   bar: "bg-neon-pink",   border: "border-neon-pink" };
}

interface SignalBarProps {
  label: string;
  value: number | null | undefined;
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

export function ScoreBadge({
  overall_score,
  skill_match_score,
  semantic_relevance_score,
  competition_score,
  client_quality,
}: ScoreBadgeProps) {
  const overall = Math.max(0, Math.min(100, Math.round(overall_score)));
  const overallColours = scoreColour(overall);
  const clientQualityPct = client_quality == null ? null : Math.round(client_quality * 100);

  const signals: SignalBarProps[] = [
    { label: "Skill Match",     value: skill_match_score,        delay: 0.10 },
    { label: "ROI / Relevance", value: semantic_relevance_score, delay: 0.15 },
    { label: "Competition",     value: competition_score,         delay: 0.20 },
    { label: "Client Quality",  value: clientQualityPct,         delay: 0.25 },
  ];

  return (
    <div className="brutal-panel p-5 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">
            Match Score
          </div>
          <div className={`text-5xl font-bold font-mono leading-none ${overallColours.text}`}>
            {overall}
          </div>
        </div>
        <div className={`w-16 h-16 border-4 ${overallColours.border} flex items-center justify-center`}>
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
      <div className="h-px bg-border" />
      <div className="space-y-3">
        {signals.map((sig) => (
          <SignalBar key={sig.label} {...sig} />
        ))}
      </div>
    </div>
  );
}

export default ScoreBadge;
