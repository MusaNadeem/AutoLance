"use client";

import { motion, AnimatePresence } from "framer-motion";
import { SlidersHorizontal, X, ArrowUpDown, Clock, DollarSign, Target } from "lucide-react";
import type { JobsListParams } from "@/types";

interface FilterBarProps {
  params: JobsListParams;
  onChange: (next: Partial<JobsListParams>) => void;
  onClear: () => void;
  totalJobs?: number;
}

const SORT_OPTIONS: { value: JobsListParams["sort_by"]; label: string }[] = [
  { value: "posted_at", label: "Newest First" },
  { value: "score",     label: "Highest Score" },
  { value: "budget",    label: "Highest Budget" },
];

const TIME_OPTIONS: { value: number | undefined; label: string }[] = [
  { value: undefined, label: "Any Time" },
  { value: 24,        label: "Last 24h" },
  { value: 72,        label: "Last 3 days" },
  { value: 168,       label: "Last 7 days" },
];

function isActive(params: JobsListParams): boolean {
  return (
    params.sort_by !== "posted_at" ||
    (params.min_score !== undefined && params.min_score > 0) ||
    params.posted_within !== undefined ||
    params.budget_type !== undefined
  );
}

export function FilterBar({ params, onChange, onClear, totalJobs }: FilterBarProps) {
  const active = isActive(params);

  return (
    <div className="border-2 border-border bg-surface-800 p-4 mb-6 space-y-4">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-slate-400 font-mono text-xs font-bold uppercase tracking-widest">
          <SlidersHorizontal size={14} className="text-neon-lime" />
          Filters
          {totalJobs !== undefined && (
            <span className="ml-2 text-white">{totalJobs} jobs</span>
          )}
        </div>

        <AnimatePresence>
          {active && (
            <motion.button
              key="clear"
              initial={{ opacity: 0, scale: 0.85 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.85 }}
              transition={{ duration: 0.15 }}
              onClick={onClear}
              className="flex items-center gap-1 text-[10px] font-mono font-bold uppercase tracking-widest text-neon-pink border border-neon-pink px-2 py-1 hover:bg-neon-pink hover:text-surface-900 transition-colors"
            >
              <X size={10} /> Clear All
            </motion.button>
          )}
        </AnimatePresence>
      </div>

      {/* Filter controls */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Sort by */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1 text-[10px] font-mono font-bold uppercase tracking-widest text-slate-500">
            <ArrowUpDown size={10} /> Sort By
          </label>
          <select
            id="filter-sort-by"
            value={params.sort_by ?? "posted_at"}
            onChange={(e) => onChange({ sort_by: e.target.value as JobsListParams["sort_by"] })}
            className="w-full bg-surface-900 border-2 border-border text-white font-mono text-xs px-2 py-1.5 focus:outline-none focus:border-neon-lime transition-colors"
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>

        {/* Min Score */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1 text-[10px] font-mono font-bold uppercase tracking-widest text-slate-500">
            <Target size={10} /> Min Score: <span className="text-neon-lime">{params.min_score ?? 0}</span>
          </label>
          <input
            id="filter-min-score"
            type="range"
            min={0}
            max={100}
            step={5}
            value={params.min_score ?? 0}
            onChange={(e) => {
              const val = Number(e.target.value);
              onChange({ min_score: val > 0 ? val : undefined });
            }}
            className="w-full accent-[#ccff00] cursor-pointer"
          />
        </div>

        {/* Budget type */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1 text-[10px] font-mono font-bold uppercase tracking-widest text-slate-500">
            <DollarSign size={10} /> Budget Type
          </label>
          <div className="flex gap-1">
            {(["all", "hourly", "fixed"] as const).map((opt) => {
              const selected =
                opt === "all" ? !params.budget_type : params.budget_type === opt;
              return (
                <button
                  id={`filter-budget-${opt}`}
                  key={opt}
                  onClick={() => onChange({ budget_type: opt === "all" ? undefined : opt })}
                  className={`flex-1 py-1.5 text-[10px] font-mono font-bold uppercase border-2 transition-colors ${
                    selected
                      ? "bg-neon-lime text-surface-900 border-neon-lime"
                      : "bg-surface-900 text-slate-400 border-border hover:border-neon-lime"
                  }`}
                >
                  {opt}
                </button>
              );
            })}
          </div>
        </div>

        {/* Posted within */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1 text-[10px] font-mono font-bold uppercase tracking-widest text-slate-500">
            <Clock size={10} /> Posted Within
          </label>
          <select
            id="filter-posted-within"
            value={params.posted_within ?? ""}
            onChange={(e) =>
              onChange({ posted_within: e.target.value ? Number(e.target.value) : undefined })
            }
            className="w-full bg-surface-900 border-2 border-border text-white font-mono text-xs px-2 py-1.5 focus:outline-none focus:border-neon-lime transition-colors"
          >
            {TIME_OPTIONS.map((o) => (
              <option key={o.value ?? "any"} value={o.value ?? ""}>{o.label}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
