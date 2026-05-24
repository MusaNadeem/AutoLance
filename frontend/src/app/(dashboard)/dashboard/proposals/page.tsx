"use client";

import { motion } from "framer-motion";
import { DollarSign, Trophy } from "lucide-react";

const COLUMNS = [
  { id: "drafted", label: "Drafted", color: "border-slate-500/30 bg-slate-500/5" },
  { id: "sent", label: "Sent", color: "border-blue-500/30 bg-blue-500/5" },
  { id: "viewed", label: "Viewed", color: "border-brand-500/30 bg-brand-500/5" },
  { id: "replied", label: "Replied", color: "border-violet-500/30 bg-violet-500/5" },
  { id: "interview", label: "Interview", color: "border-amber-500/30 bg-amber-500/5" },
  { id: "won", label: "Won 🎉", color: "border-emerald-500/30 bg-emerald-500/5" },
  { id: "lost", label: "Lost", color: "border-red-500/30 bg-red-500/5" },
];

const initialProposals = [
  { id: "p1", status: "won", title: "Python Data Pipeline — FinTech", bid: "$4,000", match: 91, client: "DataCorp Inc" },
  { id: "p2", status: "interview", title: "React Dashboard for AI Platform", bid: "$65/hr", match: 88, client: "AIVision" },
  { id: "p3", status: "replied", title: "FastAPI Microservices Architecture", bid: "$6,500", match: 84, client: "ScaleCo" },
  { id: "p4", status: "sent", title: "Next.js SaaS Boilerplate", bid: "$3,200", match: 79, client: "StartupHub" },
  { id: "p5", status: "drafted", title: "TypeScript SDK Development", bid: "$4,800", match: 76, client: "DevTools Co" },
  { id: "p6", status: "lost", title: "Vue.js E-commerce Frontend", bid: "$2,800", match: 62, client: "ShopNow" },
];

const matchColors = (score: number) => score >= 85 ? "text-emerald-400" : score >= 70 ? "text-brand-400" : "text-amber-400";

export default function ProposalsPage() {
  const proposals = initialProposals;

  return (
    <div className="p-6 space-y-6 h-full flex flex-col">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Proposal Tracker</h1>
          <p className="text-slate-400 mt-1">Track every proposal from draft to close</p>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <div className="glass-card px-4 py-2 flex items-center gap-2">
            <Trophy size={14} className="text-emerald-400" />
            <span className="text-white font-semibold">31%</span>
            <span className="text-slate-400">win rate</span>
          </div>
          <div className="glass-card px-4 py-2 flex items-center gap-2">
            <DollarSign size={14} className="text-amber-400" />
            <span className="text-white font-semibold">$4,200</span>
            <span className="text-slate-400">avg value</span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-x-auto">
        <div className="flex gap-4 min-w-max pb-4">
          {COLUMNS.map((col) => {
            const colProposals = proposals.filter((p) => p.status === col.id);
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
                  {colProposals.map((proposal) => (
                    <motion.div
                      key={proposal.id}
                      layout
                      className="bg-surface-3 border border-surface-5 rounded-xl p-3 cursor-pointer hover:border-brand-500/30 transition-all duration-200"
                    >
                      <p className="text-sm text-white font-medium leading-snug mb-2">{proposal.title}</p>
                      <p className="text-xs text-slate-500 mb-2">{proposal.client}</p>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-white">{proposal.bid}</span>
                        <span className={`text-xs font-mono font-bold ${matchColors(proposal.match)}`}>
                          {proposal.match}%
                        </span>
                      </div>
                    </motion.div>
                  ))}

                  {colProposals.length === 0 && (
                    <div className="h-16 rounded-xl border-2 border-dashed border-surface-5 flex items-center justify-center">
                      <span className="text-xs text-slate-600">Drop here</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
