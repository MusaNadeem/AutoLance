/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import useSWR from "swr";
import { fetcher, proposals as proposalsApi, scrape } from "@/lib/api";
import {
  TrendingUp, Target, Zap, Trophy, ArrowUp, ArrowRight,
  Clock, Users, DollarSign, Activity, X, Shield, Sparkles, Loader2,
} from "lucide-react";
import { ScoreBadge } from "@/components/jobs/ScoreBadge";
import { BidRecommendation } from "@/components/jobs/BidRecommendation";
import { ProposalPanel } from "@/components/jobs/ProposalPanel";
import type { Job } from "@/types";

const statsConfig = [
  { key: "total_jobs",       label: "ACTIVE JOBS",     icon: Target,    color: "text-neon-lime"   },
  { key: "win_rate",         label: "WIN RATE",         icon: Trophy,    color: "text-neon-cyan"   },
  { key: "sent",             label: "PROPOSALS SENT",   icon: TrendingUp,color: "text-neon-pink"   },
  { key: "total_revenue",    label: "PIPELINE VALUE",   icon: DollarSign,color: "text-neon-orange" },
];

const tierColors: Record<string, string> = {
  high: "badge-high",
  medium: "badge-medium",
  risky: "badge-risky",
  avoid: "badge-avoid",
};

function ScoreRing({ score }: { score: number }) {
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (score / 100) * circumference;
  const color = score >= 85 ? "#ccff00" : score >= 70 ? "#00e5ff" : "#ff4500";

  return (
    <div className="relative w-20 h-20 shrink-0">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r={radius} fill="none" stroke="#2e2e2e" strokeWidth="6" />
        <circle
          cx="40" cy="40" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="square"
          className="score-ring transition-all duration-1000"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="font-bold font-display text-white text-lg tracking-tighter">{score}</span>
      </div>
    </div>
  );
}

const STATUS_COLORS: Record<string, string> = {
  drafted:   "text-slate-400 border-slate-500",
  sent:      "text-neon-orange border-neon-orange",
  viewed:    "text-neon-cyan border-neon-cyan",
  replied:   "text-violet-400 border-violet-400",
  interview: "text-amber-400 border-amber-400",
  won:       "text-neon-lime border-neon-lime",
  lost:      "text-red-400 border-red-400",
};

function ProposalPipelineWidget() {
  const { data: list } = useSWR(
    "/proposals-dashboard",
    () => proposalsApi.list().then((r) => r.data),
    { revalidateOnFocus: false }
  );
  const recent = (list ?? []).slice(0, 4) as Array<{
    id: string; job_title: string | null; status: string; bid_amount: number | null;
  }>;

  return (
    <div className="brutal-panel p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-display font-bold text-white uppercase tracking-wide">Proposal Pipeline</h3>
        <a href="/dashboard/proposals" className="text-neon-lime text-xs font-mono font-bold hover:underline">View all →</a>
      </div>
      <div className="space-y-3">
        {recent.length === 0 ? (
          <p className="text-slate-500 text-sm font-mono text-center py-4">
            No proposals yet — use Apply + Track in the jobs feed.
          </p>
        ) : (
          recent.map((p) => (
            <div key={p.id} className="flex items-center gap-4 p-2">
              <span className={`text-xs px-2 py-1 border-2 font-mono font-bold uppercase tracking-wider w-24 text-center shrink-0 ${STATUS_COLORS[p.status] ?? "text-slate-400 border-slate-500"}`}>
                {p.status}
              </span>
              <span className="text-sm font-bold text-slate-300 flex-1 truncate">{p.job_title ?? "Untitled"}</span>
              <span className="text-sm font-mono font-bold text-white shrink-0">
                {p.bid_amount ? `$${Number(p.bid_amount).toLocaleString()}` : "—"}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [scraping, setScraping] = useState(false);

  const handleTriggerScrape = async () => {
    setScraping(true);
    try {
      await scrape.trigger();
      alert("Scraping started! Your dashboard will populate with jobs in a few minutes.");
    } catch {
      alert("Failed to trigger scrape. Check your API settings.");
    } finally {
      setScraping(false);
    }
  };

  const timeAgo = (input: string | Date) => {
    const date = typeof input === "string" ? new Date(input) : input;
    const diffMs = Date.now() - date.getTime();
    const diffMinutes = Math.max(0, Math.floor(diffMs / 60000));
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const hours = Math.floor(diffMinutes / 60);
    return `${hours}h ago`;
  };

  const { data: jobsData, isLoading: jobsLoading } = useSWR("/jobs?sort_by=score&limit=5", fetcher, {
    revalidateOnFocus: false,
    shouldRetryOnError: false,
  });
  const { data: statsData, isLoading: statsLoading } = useSWR("/proposals/analytics", fetcher, {
    revalidateOnFocus: false,
    shouldRetryOnError: false,
  });
  const { data: alertEventsData } = useSWR("/alerts/events", fetcher, {
    revalidateOnFocus: false,
    shouldRetryOnError: false,
  });

  const recentAlerts = Array.isArray(alertEventsData) ? alertEventsData : [];
  const jobs: Job[] = jobsData?.jobs ?? [];

  const handleJobClick = (job: Job) => setSelectedJob(job);

  const handleAlertClick = (alert: any) => {
    const match = jobs.find((j) => j.id === alert.job_id);
    if (match) setSelectedJob(match);
    else router.push("/dashboard/jobs");
  };

  return (
    <div className="flex h-full overflow-hidden">
      {/* ── Main content ───────────────────────────────────────────────────── */}
      <div className={`flex-1 p-6 space-y-8 overflow-y-auto transition-all duration-300 ${selectedJob ? "lg:max-w-2xl xl:max-w-3xl" : ""}`}>
        {/* Welcome */}
        <div className="border-l-4 border-neon-lime pl-4">
          <h1 className="text-3xl font-display font-bold text-white uppercase tracking-tight">Your Match Intelligence</h1>
          <p className="text-slate-400 mt-2 font-mono text-sm uppercase tracking-wider flex items-center gap-2">
            <Activity size={14} className="text-neon-lime" />
            {jobs.length} jobs scored against your profile
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          {statsConfig.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1, duration: 0.4, ease: "easeOut" }}
              className="brutal-panel p-5 group"
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-slate-400 font-mono text-xs font-bold mb-2 tracking-widest">{stat.label}</p>
                  <p className="text-3xl font-display font-bold text-white group-hover:text-neon-lime transition-colors">
                    {statsLoading ? "—" : (() => {
                      const v = stat.key === "total_jobs"
                        ? (jobsData?.total ?? 0)
                        : (statsData as Record<string, unknown>)?.[stat.key];
                      if (v == null) return "—";
                      if (stat.key === "win_rate") return `${v}%`;
                      if (stat.key === "total_revenue") return `$${Number(v).toLocaleString()}`;
                      return String(v);
                    })()}
                  </p>
                </div>
                <div className={`w-10 h-10 border-2 border-surface-600 bg-surface-900 flex items-center justify-center ${stat.color} group-hover:border-neon-lime transition-colors`}>
                  <stat.icon size={20} strokeWidth={2.5} />
                </div>
              </div>
              <div className="flex items-center gap-1 mt-4 text-neon-lime font-mono text-xs font-bold">
                <ArrowUp size={14} strokeWidth={3} />
                LIVE
              </div>
            </motion.div>
          ))}
        </div>

        {/* Top Matches */}
        <div>
          <div className="flex items-center justify-between mb-6 border-b-2 border-border pb-2">
            <h2 className="text-xl font-display font-bold text-white uppercase tracking-wide">Top Matches Right Now</h2>
            <a href="/dashboard/jobs" className="text-neon-lime hover:text-white text-sm font-mono font-bold flex items-center gap-1 transition-colors uppercase">
              View all feed <ArrowRight size={16} strokeWidth={2.5} />
            </a>
          </div>

          <div className="space-y-4">
            {jobsLoading ? (
              <div className="h-32 skeleton border-2 border-border" />
            ) : jobs.length === 0 ? (
              <div className="text-center py-12 space-y-6 border-2 border-dashed border-border bg-surface-900/50 backdrop-blur-sm rounded-xl">
                <div className="w-16 h-16 bg-surface-800 border-2 border-border flex items-center justify-center mx-auto rounded-full mb-4 shadow-brutal-sm">
                  <Activity className="w-8 h-8 text-neon-pink opacity-80" />
                </div>
                <h3 className="text-xl font-display font-bold text-white uppercase tracking-wide">Ready to find work?</h3>
                <p className="text-slate-400 text-sm font-mono max-w-sm mx-auto">Your database is currently empty. Trigger a scrape to pull the latest personalized jobs from Upwork.</p>
                <button 
                  onClick={handleTriggerScrape}
                  disabled={scraping}
                  className="btn-primary flex items-center gap-2 mx-auto px-6 py-3"
                >
                  {scraping ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
                  <span>{scraping ? "TRIGGERING..." : "TRIGGER SCRAPE"}</span>
                </button>
              </div>
            ) : (
              jobs.slice(0, 3).map((job: any, i: number) => {
                const score = typeof job.score === "number"
                  ? job.score
                  : Math.round(((job.score as { overall?: number | null })?.overall ?? 0) * 100);
                const isSelected = selectedJob?.id === job.id;

                return (
                  <motion.div
                    key={job.id}
                    initial={{ opacity: 0, x: -24 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 + 0.2, duration: 0.3, ease: "easeOut" }}
                    className={`brutal-panel p-5 cursor-pointer group transition-all duration-150 ${isSelected ? "border-neon-lime translate-x-1" : ""}`}
                    onClick={() => handleJobClick(job)}
                  >
                    <div className="flex items-start gap-5">
                      <ScoreRing score={score} />

                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-3">
                          <h3 className={`font-display font-bold text-lg transition-colors truncate ${isSelected ? "text-neon-lime" : "text-white group-hover:text-neon-lime"}`}>
                            {job.title}
                          </h3>
                          <div className="flex items-center gap-2 shrink-0">
                            {score > 90 && (
                              <span className="flex items-center gap-1 px-2 py-1 bg-neon-lime text-surface-900 border-2 border-neon-lime font-mono text-xs font-bold uppercase tracking-wider">
                                <Zap size={12} strokeWidth={3} />
                                Easy Win
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="flex flex-wrap items-center gap-4 mt-3">
                          <span className="text-white font-mono font-bold text-sm bg-surface-900 px-2 py-1 border border-border">
                            {job.budget_type === "fixed" ? `$${job.budget_min} - $${job.budget_max}` : `$${job.budget_min}/hr`}
                          </span>
                          <span className="text-slate-400 text-xs font-mono font-bold uppercase flex items-center gap-1">
                            <Users size={14} /> {job.proposal_count || "0"} proposals
                          </span>
                          <span className="text-slate-400 text-xs font-mono font-bold uppercase flex items-center gap-1">
                            <Clock size={14} /> 2h ago
                          </span>
                          <span className={`${tierColors[job.clientTier as string || "high"]}`}>
                            {(job.client as any)?.history || "15+ hires, $10k+ spent"}
                          </span>
                        </div>

                        <div className="flex items-center gap-2 mt-4">
                          {((() => {
                            const raw = job.required_skills;
                            if (!raw) return ["React", "FastAPI"];
                            if (Array.isArray(raw)) return raw;
                            try { return JSON.parse(raw as string); }
                            catch { return (raw as string).split(",").map((s: string) => s.trim()); }
                          })() as string[]).slice(0, 3).map((skill: string) => (
                            <span key={skill} className="px-2 py-1 border-2 border-surface-600 bg-surface-900 text-slate-300 font-mono text-xs font-bold">
                              {skill}
                            </span>
                          ))}
                          <button
                            className="ml-auto btn-primary text-xs py-2 px-4 opacity-0 group-hover:opacity-100 transition-opacity"
                            onClick={(e) => { e.stopPropagation(); handleJobClick(job); }}
                          >
                            Generate Cover Letter
                          </button>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })
            )}
          </div>
        </div>

        {/* Activity feed */}
        <div className="grid lg:grid-cols-2 gap-8 pt-4">
          {/* Recent alerts */}
          <div className="brutal-panel p-6">
            <h3 className="font-display font-bold text-white mb-6 uppercase tracking-wide flex items-center gap-3">
              <div className="w-3 h-3 bg-neon-pink border-2 border-border animate-blink" />
              Recent Alerts
            </h3>
            <div className="space-y-4">
              {recentAlerts.length === 0 ? (
                <p className="text-slate-500 text-sm font-mono text-center py-4">No alerts yet — high-scoring jobs will appear here.</p>
              ) : (
                recentAlerts.slice(0, 4).map((alert: any) => (
                  <div
                    key={alert.id}
                    className="flex items-center gap-4 p-3 border-2 border-transparent hover:border-neon-pink bg-surface-900 transition-colors cursor-pointer"
                    onClick={() => handleAlertClick(alert)}
                  >
                    <div className="w-12 h-12 bg-surface-800 border-2 border-border flex items-center justify-center shrink-0">
                      <span className="text-neon-pink font-bold font-mono text-lg">{alert.match_score ?? "—"}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-bold text-white truncate">{alert.job_title || "Untitled job"}</p>
                      <p className="text-xs font-mono text-slate-500 uppercase mt-1">{alert.sent_at ? timeAgo(alert.sent_at) : ""}</p>
                    </div>
                    <ArrowRight size={18} className="text-slate-500 shrink-0" strokeWidth={2.5} />
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Proposal pipeline — real data */}
          <ProposalPipelineWidget />
        </div>
      </div>

      {/* ── Job detail side panel ────────────────────────────────────────────── */}
      <AnimatePresence>
        {selectedJob && (
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 40 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="hidden lg:flex w-[500px] xl:w-[580px] border-l-2 border-border flex-col bg-surface-900 overflow-hidden"
          >
            {/* Panel header */}
            <div className="p-6 border-b-2 border-border flex items-start justify-between bg-surface-800 shrink-0">
              <h2 className="text-base font-display font-bold text-white leading-snug flex-1 pr-4 uppercase tracking-wide">
                {selectedJob.title}
              </h2>
              <button
                onClick={() => setSelectedJob(null)}
                className="text-slate-400 hover:text-neon-pink transition-colors shrink-0"
              >
                <X size={22} strokeWidth={2.5} />
              </button>
            </div>

            {/* Panel body */}
            <div className="p-6 space-y-6 flex-1 overflow-y-auto">
              <ScoreBadge score={selectedJob.score} />

              <BidRecommendation
                bid={(selectedJob as any).bid ?? null}
                budget_type={selectedJob.budget_type}
              />

              {/* Client info */}
              <div className="brutal-panel p-5">
                <h3 className="font-display font-bold text-white mb-4 uppercase tracking-wider flex items-center gap-3">
                  <Shield size={16} strokeWidth={2.5} className="text-neon-cyan" />
                  Client Quality
                </h3>
                <div className="grid grid-cols-3 gap-3 text-center">
                  {[
                    { label: "Total Spent", value: selectedJob.client?.total_spent != null ? `$${selectedJob.client.total_spent.toLocaleString()}` : "N/A" },
                    { label: "Hire Rate",   value: selectedJob.client?.hire_rate != null ? `${selectedJob.client.hire_rate}%` : "N/A" },
                    { label: "Rating",      value: selectedJob.client?.average_rating != null ? `⭐ ${selectedJob.client.average_rating}` : "—" },
                  ].map((c) => (
                    <div key={c.label} className="border-2 border-border bg-surface-900 p-2">
                      <div className="text-slate-400 font-mono text-[10px] font-bold uppercase mb-1">{c.label}</div>
                      <div className="font-bold font-mono text-white text-sm">{c.value}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Description */}
              {selectedJob.description && (
                <div className="border-l-4 border-neon-cyan pl-4">
                  <h3 className="font-display font-bold text-white mb-3 uppercase tracking-wider">Job Description</h3>
                  <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap line-clamp-6">
                    {selectedJob.description}
                  </p>
                </div>
              )}

              {/* Skills */}
              {selectedJob.required_skills && selectedJob.required_skills.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {(Array.isArray(selectedJob.required_skills)
                    ? selectedJob.required_skills
                    : (() => { try { return JSON.parse(selectedJob.required_skills as unknown as string); } catch { return (selectedJob.required_skills as unknown as string).split(",").map((s: string) => s.trim()); } })()
                  ).map((s: string) => (
                    <span key={s} className="px-3 py-1 bg-surface-800 border-2 border-border text-slate-300 font-mono text-xs font-bold uppercase">
                      {s}
                    </span>
                  ))}
                </div>
              )}

              {/* AI Proposal */}
              <div className="brutal-panel p-5">
                <h3 className="font-display font-bold text-white mb-4 uppercase tracking-wider flex items-center gap-3">
                  <Sparkles size={16} className="text-neon-lime" strokeWidth={2.5} />
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
