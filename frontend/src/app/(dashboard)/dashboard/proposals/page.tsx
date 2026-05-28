"use client";

import useSWR, { mutate } from "swr";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { DollarSign, Trophy, TrendingUp, ChevronDown, Loader2, FileText, Target, MessageSquare, Download } from "lucide-react";
import { proposals } from "@/lib/api";

const COLUMNS = [
  { id: "drafted",   label: "Drafted",       color: "border-slate-500/30 bg-slate-500/5" },
  { id: "sent",      label: "Sent",          color: "border-blue-500/30 bg-blue-500/5" },
  { id: "viewed",    label: "Viewed",        color: "border-brand-500/30 bg-brand-500/5" },
  { id: "replied",   label: "Replied",       color: "border-violet-500/30 bg-violet-500/5" },
  { id: "interview", label: "Interview",     color: "border-amber-500/30 bg-amber-500/5" },
  { id: "won",       label: "Won 🎉",        color: "border-emerald-500/30 bg-emerald-500/5" },
  { id: "lost",      label: "Lost",          color: "border-red-500/30 bg-red-500/5" },
];

const VALID_STATUSES = ["drafted", "sent", "viewed", "replied", "interview", "won", "lost"];

const matchColors = (score: number | null) =>
  !score ? "text-slate-500" :
  score >= 85 ? "text-emerald-400" :
  score >= 70 ? "text-brand-400" : "text-amber-400";

interface Proposal {
  id: string;
  job_id: string;
  job_title: string | null;
  job_url: string | null;
  status: string;
  bid_amount: number | null;
  bid_type: string | null;
  match_score: number | null;
  outcome_value: number | null;
  created_at: string;
}

interface Analytics {
  total: number;
  sent: number;
  replied: number;
  won: number;
  lost: number;
  win_rate: number;
  response_rate: number;
  total_revenue: number;
  avg_project_value: number;
}

export default function ProposalsPage() {
  const [movingId, setMovingId] = useState<string | null>(null);
  const [openMenu, setOpenMenu] = useState<string | null>(null);

  const { data: proposalList, isLoading } = useSWR<Proposal[]>(
    "/proposals-list",
    () => proposals.list().then((r) => r.data),
    { revalidateOnFocus: false }
  );

  const { data: analytics } = useSWR<Analytics>(
    "/proposals-analytics",
    () => proposals.analytics().then((r) => r.data),
    { revalidateOnFocus: false }
  );

  const handleMove = async (proposalId: string, newStatus: string) => {
    setMovingId(proposalId);
    setOpenMenu(null);
    try {
      await proposals.updateStatus(proposalId, newStatus);
      mutate("/proposals-list");
      mutate("/proposals-analytics");
    } finally {
      setMovingId(null);
    }
  };

  const allProposals = proposalList ?? [];
  const isEmpty = !isLoading && allProposals.length === 0;

  return (
    <div className="p-6 space-y-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Proposal Tracker</h1>
          <p className="text-slate-400 mt-1">Track every proposal from draft to close</p>
        </div>

        {/* Stats + CSV export */}
        <div className="flex items-center gap-3 text-sm flex-wrap">
          <div className="glass-card px-4 py-2 flex items-center gap-2">
            <Trophy size={14} className="text-emerald-400" />
            <span className="text-white font-semibold">{analytics?.win_rate ?? 0}%</span>
            <span className="text-slate-400">win rate</span>
          </div>
          <div className="glass-card px-4 py-2 flex items-center gap-2">
            <TrendingUp size={14} className="text-violet-400" />
            <span className="text-white font-semibold">{analytics?.response_rate ?? 0}%</span>
            <span className="text-slate-400">response</span>
          </div>
          <div className="glass-card px-4 py-2 flex items-center gap-2">
            <DollarSign size={14} className="text-amber-400" />
            <span className="text-white font-semibold">
              ${((analytics?.total_revenue ?? 0) / 1000).toFixed(1)}k
            </span>
            <span className="text-slate-400">revenue</span>
          </div>
          <a
            href="/api/v1/proposals/export?format=csv"
            download="proposals.csv"
            className="flex items-center gap-1.5 px-3 py-2 border border-border text-slate-400 hover:text-neon-lime hover:border-neon-lime font-mono text-xs uppercase tracking-widest transition-colors"
          >
            <Download size={12} /> Export CSV
          </a>
        </div>
      </div>

      {/* Funnel chart — only show when there's data */}
      {analytics && analytics.sent > 0 && (
        <div className="glass-card p-4">
          <p className="text-xs font-mono font-bold text-slate-500 uppercase tracking-widest mb-3">Pipeline Funnel</p>
          <div className="flex items-end gap-2 h-16">
            {[
              { label: "Sent",      value: analytics.sent,     color: "bg-blue-500" },
              { label: "Replied",   value: analytics.replied,  color: "bg-violet-500" },
              { label: "Won",       value: analytics.won,      color: "bg-emerald-500" },
              { label: "Lost",      value: analytics.lost,     color: "bg-red-500/60" },
            ].map(({ label, value, color }) => {
              const pct = analytics.sent > 0 ? Math.round((value / analytics.sent) * 100) : 0;
              return (
                <div key={label} className="flex flex-col items-center gap-1 flex-1">
                  <span className="text-[10px] font-mono text-slate-400">{value}</span>
                  <div className="w-full flex items-end justify-center">
                    <div
                      className={`w-full ${color} rounded-sm transition-all`}
                      style={{ height: `${Math.max(4, pct)}px` }}
                    />
                  </div>
                  <span className="text-[9px] font-mono text-slate-500 uppercase">{label}</span>
                </div>
              );
            })}
            <div className="flex flex-col items-center gap-1 flex-1">
              <span className="text-[10px] font-mono text-neon-lime font-bold">{analytics.win_rate}%</span>
              <div className="w-full flex items-end justify-center">
                <div className="w-full bg-neon-lime/20 border border-neon-lime/40 rounded-sm" style={{ height: `${Math.max(4, analytics.win_rate)}px` }} />
              </div>
              <span className="text-[9px] font-mono text-neon-lime uppercase">Win %</span>
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {isEmpty && (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center">
          <div className="w-16 h-16 rounded-2xl bg-surface-4 border border-surface-5 flex items-center justify-center">
            <FileText size={28} className="text-slate-500" />
          </div>
          <div>
            <p className="text-white font-semibold text-lg">No proposals yet</p>
            <p className="text-slate-400 text-sm mt-1">
              Apply to a job from the{" "}
              <a href="/dashboard/jobs" className="text-brand-400 hover:underline">jobs feed</a>
              {" "}to start tracking your proposals.
            </p>
          </div>
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="flex-1 flex items-center justify-center">
          <Loader2 size={28} className="animate-spin text-brand-400" />
        </div>
      )}

      {/* Kanban board */}
      {!isLoading && !isEmpty && (
        <div className="flex-1 overflow-x-auto">
          <div className="flex gap-4 min-w-max pb-4">
            {COLUMNS.map((col) => {
              const colProposals = allProposals.filter((p) => p.status === col.id);
              return (
                <div key={col.id} className={`w-64 rounded-2xl border ${col.color} flex flex-col`}>
                  <div className="p-3 border-b border-white/5">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-white">{col.label}</span>
                      <span className="w-5 h-5 rounded-full bg-surface-4 text-slate-400 text-xs flex items-center justify-center">
                        {colProposals.length}
                      </span>
                    </div>
                  </div>

                  <div className="p-2 space-y-2 flex-1">
                    <AnimatePresence>
                      {colProposals.map((proposal) => (
                        <motion.div
                          key={proposal.id}
                          layout
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: movingId === proposal.id ? 0.4 : 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.95 }}
                          className="bg-surface-3 border border-surface-5 rounded-xl p-3 relative"
                        >
                          <p className="text-sm text-white font-medium leading-snug mb-1 pr-6">
                            {proposal.job_title ?? "Untitled job"}
                          </p>
                          <div className="flex items-center justify-between mt-2">
                            <span className="text-sm font-semibold text-white">
                              {proposal.bid_amount
                                ? `$${proposal.bid_amount.toLocaleString()}`
                                : "—"}
                            </span>
                            <span className={`text-xs font-mono font-bold ${matchColors(proposal.match_score)}`}>
                              {proposal.match_score != null ? `${proposal.match_score}%` : "—"}
                            </span>
                          </div>

                          {/* Move menu */}
                          <div className="mt-2 relative">
                            <button
                              onClick={() => setOpenMenu(openMenu === proposal.id ? null : proposal.id)}
                              className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-white transition-colors font-mono uppercase tracking-widest"
                            >
                              Move <ChevronDown size={10} />
                            </button>
                            {openMenu === proposal.id && (
                              <div className="absolute bottom-full left-0 mb-1 bg-surface-2 border border-surface-5 rounded-xl shadow-xl z-20 min-w-[140px] py-1">
                                {VALID_STATUSES.filter((s) => s !== proposal.status).map((s) => (
                                  <button
                                    key={s}
                                    onClick={() => handleMove(proposal.id, s)}
                                    className="w-full text-left px-3 py-1.5 text-xs text-slate-300 hover:text-white hover:bg-surface-4 capitalize font-mono"
                                  >
                                    {s}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        </motion.div>
                      ))}
                    </AnimatePresence>

                    {colProposals.length === 0 && (
                      <div className="h-16 rounded-xl border-2 border-dashed border-surface-5 flex items-center justify-center">
                        <span className="text-xs text-slate-600">Empty</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
