"use client";

import { motion } from "framer-motion";
import type { BidRecommendation as BidRecommendationType, BudgetType } from "@/types";

const STRATEGY_STYLES = {
  Competitive: { bg: "bg-blue-500/20",    border: "border-blue-500",  text: "text-blue-400"    },
  Value:       { bg: "bg-neon-lime/20",   border: "border-neon-lime", text: "text-neon-lime"   },
  Premium:     { bg: "bg-purple-500/20",  border: "border-purple-400", text: "text-purple-400" },
} as const;

function confidenceColour(value: number): string {
  if (value >= 0.70) return "bg-neon-lime";
  if (value >= 0.40) return "bg-neon-orange";
  return "bg-neon-pink";
}

interface BidRecommendationProps {
  bid: BidRecommendationType | null | undefined;
  budget_type?: BudgetType;
}

function BidSkeleton() {
  return (
    <div className="brutal-panel p-5 space-y-4 animate-pulse" aria-label="Bid recommendation loading">
      <div className="h-3 w-24 skeleton" />
      <div className="h-10 w-36 skeleton" />
      <div className="h-3 w-16 skeleton" />
      <div className="h-2 w-full skeleton" />
      <div className="h-3 w-full skeleton" />
      <div className="h-3 w-3/4 skeleton" />
    </div>
  );
}

export function BidRecommendation({ bid, budget_type }: BidRecommendationProps) {
  if (!bid) return <BidSkeleton />;

  const suffix = budget_type === "hourly" ? "/hr" : "";
  const strategy = bid.strategy;
  const strategyStyle = strategy ? STRATEGY_STYLES[strategy] : null;
  const confidence = bid.confidence ?? 0;
  const confPct = Math.round(confidence * 100);

  return (
    <div className="brutal-panel p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-display font-bold text-white uppercase tracking-wider text-sm">
          Bid Recommendation
        </h3>
        {strategyStyle && strategy && (
          <span className={`px-2.5 py-1 border text-xs font-bold font-mono uppercase tracking-wider ${strategyStyle.bg} ${strategyStyle.border} ${strategyStyle.text}`}>
            {strategy}
          </span>
        )}
      </div>

      {bid.recommended != null ? (
        <div className="text-4xl font-bold font-mono text-neon-lime">
          ${bid.recommended.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          {suffix && <span className="text-xl font-mono text-slate-400 ml-1">{suffix}</span>}
        </div>
      ) : (
        <div className="text-4xl font-bold font-mono text-slate-500">—</div>
      )}

      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-slate-400">
            Win Confidence
          </span>
          <span className="font-mono text-xs font-bold text-slate-300">{confPct}%</span>
        </div>
        <div className="h-1.5 bg-surface-800 border border-border overflow-hidden">
          <motion.div
            className={confidenceColour(confidence)}
            style={{ height: "100%" }}
            initial={{ width: 0 }}
            animate={{ width: `${confPct}%` }}
            transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 }}
          />
        </div>
      </div>

      {bid.rationale && (
        <p className="text-slate-400 text-sm leading-relaxed">{bid.rationale}</p>
      )}

      {bid.range && (
        <p className="text-slate-500 text-xs font-mono">{bid.range}</p>
      )}
    </div>
  );
}

export default BidRecommendation;
