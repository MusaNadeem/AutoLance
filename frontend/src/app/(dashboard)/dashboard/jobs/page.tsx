"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import type { Job } from "@/types";
import { ScoreBadge } from "@/components/jobs/ScoreBadge";
import { BidRecommendation } from "@/components/jobs/BidRecommendation";
import { ProposalPanel } from "@/components/jobs/ProposalPanel";
import {
  Filter, Clock, Users, DollarSign,
  Zap, Shield, ShieldAlert, ShieldX, X,
  Sparkles, ExternalLink,
} from "lucide-react";

// ── Tier config ───────────────────────────────────────────────────────────────

const tierConfig: Record<string, {
  label: string;
  badge: string;
  icon: React.ComponentType<{ size?: number; strokeWidth?: number }>;
}> = {
  high: { label: "High Quality", badge: "badge-high", icon: Shield },
  medium: { label: "Medium", badge: "badge-medium", icon: Shield },
  risky: { label: "Risky", badge: "badge-risky", icon: ShieldAlert },
  avoid: { label: "Avoid", badge: "badge-avoid", icon: ShieldX },
};

// ── Compact score bar for the list cards ─────────────────────────────────────

function CompactScoreBar({ score }: { score: number }) {
  const colour =
    score >= 85 ? "bg-neon-lime" :
      score >= 70 ? "bg-neon-cyan" :
        score >= 50 ? "bg-neon-orange" :
          "bg-neon-pink";
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-3 bg-surface-800 border-2 border-border overflow-hidden">
        <motion.div
          className={`h-full ${colour}`}
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 }}
        />
      </div>
      <span className={`text-sm font-bold font-mono w-8 text-right ${colour.replace("bg-", "text-")}`}>
        {score}
      </span>
    </div>
  );
}

// ── Demo fallback data (matches Job interface) ────────────────────────────────

const DEMO_JOBS: Job[] = [
  {
    id: "demo-1",
    upwork_job_id: "demo-1",
    title: "FastAPI Backend — Real-Time Analytics",
    description:
      "Build a high-throughput FastAPI backend with Redis caching and Postgres analytics queries.",
    budget_type: "hourly",
    budget_min: 75,
    budget_max: 110,
    proposal_count: 6,
    proposal_tier: "low",
    required_skills: ["FastAPI", "PostgreSQL", "Redis"],
    scraped_at: new Date().toISOString(),
    score: { overall: 0.88, skill_match: 0.92, roi: 0.85, competition: 0.90, client_quality: 0.82 },
    bid: {
      recommended: 95,
      range_min: 85.5,
      range_max: 104.5,
      range: "$85.50 – $104.50 acceptable range",
      strategy: "Value",
      rationale:
        "Bidding $95.00/hr using a Value strategy. The client's budget is above your target rate. Low competition detected (6 proposals).",
      confidence: 0.85,
    },
  },
  {
    id: "demo-2",
    upwork_job_id: "demo-2",
    title: "React Native Developer for FinTech App",
    description: "Implement core flows for a fintech mobile app and integrate with REST APIs.",
    budget_type: "fixed",
    budget_min: 2500,
    budget_max: 4500,
    proposal_count: 14,
    proposal_tier: "medium",
    required_skills: ["React Native", "TypeScript", "API Integration"],
    scraped_at: new Date().toISOString(),
    score: { overall: 0.72, skill_match: 0.75, roi: 0.68, competition: 0.65, client_quality: 0.64 },
    bid: {
      recommended: 3800,
      range_min: 3420,
      range_max: 4180,
      range: "$3,420.00 – $4,180.00 acceptable range",
      strategy: "Competitive",
      rationale:
        "Bidding $3,800.00 using a Competitive strategy based on the client's budget anchor of $4,500.00. Adjusted down for moderate competition (14 proposals).",
      confidence: 0.71,
    },
  },
  {
    id: "demo-3",
    upwork_job_id: "demo-3",
    title: "Python ML Engineer — Healthcare AI",
    description: "Train and deploy a small NLP model, build evaluation, and integrate into an API.",
    budget_type: "hourly",
    budget_min: 90,
    budget_max: 140,
    proposal_count: 3,
    proposal_tier: "low",
    required_skills: ["Python", "ML", "NLP"],
    scraped_at: new Date().toISOString(),
    score: { overall: 0.95, skill_match: 0.97, roi: 0.94, competition: 0.96, client_quality: 0.91 },
    bid: {
      recommended: 147,
      range_min: 132.3,
      range_max: 161.7,
      range: "$132.30 – $161.70 acceptable range",
      strategy: "Premium",
      rationale:
        "Bidding $147.00/hr using a Premium strategy. High-quality client (91% score); they hire consistently. Low competition (3 proposals).",
      confidence: 0.93,
    },
  },
];

// ── Page ──────────────────────────────────────────────────────────────────────

export default function JobsPage() {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [coverLetter, setCoverLetter] = useState<string | null>(null);

  const { data: jobsData, isLoading } = useSWR("/jobs", fetcher, {
    fallbackData: { jobs: DEMO_JOBS },
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
    shouldRetryOnError: false,
    errorRetryCount: 0,
  });

  const apiJobs: Job[] = jobsData?.jobs ?? [];
  const jobs: Job[] = apiJobs.length ? apiJobs : DEMO_JOBS;

  const { data: jobDetails } = useSWR<Job>(
    selectedJobId ? `/jobs/${selectedJobId}` : null,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      shouldRetryOnError: false,
      errorRetryCount: 0,
    }
  );
  const selectedJob: Job | undefined = jobDetails ?? jobs.find((j) => j.id === selectedJobId);

  // handleGenerate replaced by ProposalPanel (Phase 3)

  return (
    <div className="flex h-full max-w-7xl mx-auto">
      {/* ── Job list ─────────────────────────────────────────────────────── */}
      <div
        className={`flex-1 p-4 md:p-6 overflow-y-auto transition-all duration-300 ${selectedJobId ? "lg:max-w-md xl:max-w-lg pr-4" : ""
          }`}
      >
        <div className="flex items-center justify-between mb-8 border-b-2 border-border pb-4">
          <div>
            <h1 className="text-3xl font-display font-bold text-white uppercase tracking-tight">
              Job Feed
            </h1>
            <p className="text-slate-400 font-mono text-xs mt-2 uppercase tracking-widest flex items-center gap-2">
              <Zap size={14} className="text-neon-lime" />
              {jobs.length} active matches
            </p>
          </div>
          <button className="btn-ghost flex items-center gap-2 text-sm">
            <Filter size={16} strokeWidth={2.5} /> FILTERS
          </button>
        </div>

        <div className="space-y-4">
          {isLoading ? (
            Array(5)
              .fill(0)
              .map((_, i) => (
                <div key={i} className="h-32 skeleton border-2 border-border" />
              ))
          ) : (
            jobs.map((job, i) => {
              // Overall score: prefer score.overall (0.0-1.0 → 0-100), fall back to 0
              const scoreVal = job.score?.overall != null
                ? Math.round(job.score.overall * 100)
                : 0;
              const isEasyWin = scoreVal > 85;
              const clientTier =
                (job.score?.client_quality ?? 0) >= 0.75
                  ? "high"
                  : (job.score?.client_quality ?? 0) >= 0.50
                    ? "medium"
                    : "risky";

              return (
                <motion.div
                  key={job.id}
                  layout="position"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05, duration: 0.25, ease: "easeOut" }}
                  onClick={() => {
                    setSelectedJobId(job.id);
                  }}
                  className={`brutal-panel p-5 cursor-pointer transition-all duration-150 ${selectedJobId === job.id ? "border-neon-lime translate-x-2" : ""
                    }`}
                >
                  <div className="flex items-start justify-between gap-4 mb-4">
                    <h3 className="font-display font-bold text-white text-base leading-snug flex-1 uppercase tracking-wide">
                      {job.title}
                    </h3>
                    {isEasyWin && (
                      <span className="flex items-center gap-1 px-2 py-1 bg-neon-lime text-surface-900 border-2 border-neon-lime font-mono text-xs font-bold uppercase tracking-wider shrink-0">
                        <Zap size={12} strokeWidth={3} /> EASY WIN
                      </span>
                    )}
                  </div>

                  <CompactScoreBar score={scoreVal} />

                  <div className="flex flex-wrap gap-4 mt-5 font-mono text-xs font-bold text-slate-400 uppercase tracking-wide">
                    <span className="flex items-center gap-1 text-white">
                      <DollarSign size={14} strokeWidth={2.5} />
                      {job.budget_type === "fixed"
                        ? `$${job.budget_min ?? 0} – $${job.budget_max ?? 0}`
                        : `$${job.hourly_rate_min ?? job.budget_min ?? 0}/hr`}
                    </span>
                    <span className="flex items-center gap-1">
                      <Users size={14} strokeWidth={2.5} />
                      {job.proposal_count} PROPOSALS
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock size={14} strokeWidth={2.5} />
                      2h AGO
                    </span>
                    <span className={`px-2 py-1 ${tierConfig[clientTier].badge}`}>
                      {tierConfig[clientTier].label}
                    </span>
                  </div>
                </motion.div>
              );
            })
          )}
        </div>
      </div>

      {/* ── Job detail panel ─────────────────────────────────────────────── */}
      <AnimatePresence>
        {selectedJobId && selectedJob && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="hidden lg:flex w-[520px] xl:w-[600px] border-l-2 border-border flex-col h-full bg-surface-900"
          >
            {/* Panel header */}
            <div className="p-6 border-b-2 border-border flex items-start justify-between bg-surface-800">
              <h2 className="text-lg font-display font-bold text-white leading-snug flex-1 pr-6 uppercase tracking-wide">
                {selectedJob.title}
              </h2>
              <button
                onClick={() => setSelectedJobId(null)}
                className="text-slate-400 hover:text-neon-pink transition-colors"
              >
                <X size={24} strokeWidth={2.5} />
              </button>
            </div>

            <div className="p-6 space-y-6 flex-1 overflow-y-auto">
              {/* ScoreBadge — QA-9 & QA-10 */}
              <ScoreBadge
                score={selectedJob.score}
              />

              {/* BidRecommendation — QA-11 & QA-12 */}
              <BidRecommendation
                bid={selectedJob.bid ?? null}
                budget_type={selectedJob.budget_type}
              />

              {/* Client info */}
              <div className="brutal-panel p-5">
                <h3 className="font-display font-bold text-white mb-4 uppercase tracking-wider flex items-center gap-3">
                  <Shield size={18} strokeWidth={2.5} className="text-neon-cyan" />
                  Client Quality
                </h3>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="border-2 border-border bg-surface-900 p-2">
                    <div className="text-slate-400 font-mono text-[10px] font-bold uppercase mb-1">
                      Total Spent
                    </div>
                    <div className="font-bold font-mono text-white text-sm">
                      {selectedJob.client?.total_spent != null
                        ? `$${selectedJob.client.total_spent.toLocaleString()}`
                        : "N/A"}
                    </div>
                  </div>
                  <div className="border-2 border-border bg-surface-900 p-2">
                    <div className="text-slate-400 font-mono text-[10px] font-bold uppercase mb-1">
                      Hire Rate
                    </div>
                    <div className="font-bold font-mono text-white text-sm">
                      {selectedJob.client?.hire_rate != null
                        ? `${selectedJob.client.hire_rate}%`
                        : "N/A"}
                    </div>
                  </div>
                  <div className="border-2 border-border bg-surface-900 p-2">
                    <div className="text-slate-400 font-mono text-[10px] font-bold uppercase mb-1">
                      Rating
                    </div>
                    <div className="font-bold font-mono text-white text-sm">
                      {selectedJob.client?.average_rating != null
                        ? `⭐ ${selectedJob.client.average_rating}`
                        : "—"}
                    </div>
                  </div>
                </div>
              </div>

              {/* Description */}
              <div className="border-l-4 border-neon-cyan pl-4">
                <h3 className="font-display font-bold text-white mb-3 uppercase tracking-wider">
                  Job Description
                </h3>
                <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
                  {selectedJob.description}
                </p>
              </div>

              {/* Skill tags */}
              {selectedJob.required_skills && selectedJob.required_skills.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {(Array.isArray(selectedJob.required_skills)
                    ? selectedJob.required_skills
                    : (() => { try { return JSON.parse(selectedJob.required_skills as unknown as string); } catch { return (selectedJob.required_skills as unknown as string).split(',').map((s: string) => s.trim()); } })()
                  ).map((s: string) => (
                    <span
                      key={s}
                      className="px-3 py-1 bg-surface-800 border-2 border-border text-slate-300 font-mono text-xs font-bold uppercase"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              )}

              {/* Phase 3: ProposalPanel — tone selector, char counter, copy, Open on Upwork */}
              <div className="brutal-panel p-5">
                <h3 className="font-display font-bold text-white mb-4 uppercase tracking-wider flex items-center gap-3">
                  <Sparkles size={18} className="text-neon-lime" strokeWidth={2.5} />
                  AI Proposal
                </h3>
                <ProposalPanel job={selectedJob} />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
