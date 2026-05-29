"use client";

import React, { useState, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import useSWR from "swr";
import { fetcher, saved as savedApi } from "@/lib/api";
import type { Job, JobsListParams } from "@/types";
import { ScoreBadge } from "@/components/jobs/ScoreBadge";
import { BidRecommendation } from "@/components/jobs/BidRecommendation";
import { ProposalPanel } from "@/components/jobs/ProposalPanel";
import { FilterBar } from "@/components/jobs/FilterBar";
import {
  Clock, Users, DollarSign,
  Zap, Shield, ShieldAlert, ShieldX, X,
  Sparkles, SearchX, Bookmark, BookmarkCheck,
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


// ── Page ──────────────────────────────────────────────────────────────────────

const DEFAULTS: JobsListParams = {
  sort_by: "posted_at",
  min_score: undefined,
  posted_within: undefined,
  budget_type: undefined,
};

function paramsFromSearch(sp: URLSearchParams): JobsListParams {
  return {
    sort_by: (sp.get("sort_by") as JobsListParams["sort_by"]) || "posted_at",
    min_score: sp.has("min_score") ? Number(sp.get("min_score")) : undefined,
    posted_within: sp.has("posted_within") ? Number(sp.get("posted_within")) : undefined,
    budget_type: (sp.get("budget_type") as JobsListParams["budget_type"]) || undefined,
  };
}

function buildApiUrl(params: JobsListParams): string {
  const sp = new URLSearchParams();
  if (params.sort_by && params.sort_by !== "posted_at") sp.set("sort_by", params.sort_by);
  if (params.min_score) sp.set("min_score", String(params.min_score));
  if (params.posted_within) sp.set("posted_within", String(params.posted_within));
  if (params.budget_type) sp.set("budget_type", params.budget_type);
  const qs = sp.toString();
  return `/jobs${qs ? `?${qs}` : ""}`;
}

function JobsFeed() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [savedIds, setSavedIds]           = useState<Set<string>>(new Set());
  const [filterParams, setFilterParams] = useState<JobsListParams>(() =>
    paramsFromSearch(searchParams)
  );

  // Sync filter changes to URL
  const handleFilterChange = useCallback((next: Partial<JobsListParams>) => {
    const updated = { ...filterParams, ...next };
    setFilterParams(updated);

    const sp = new URLSearchParams();
    if (updated.sort_by && updated.sort_by !== "posted_at") sp.set("sort_by", updated.sort_by);
    if (updated.min_score) sp.set("min_score", String(updated.min_score));
    if (updated.posted_within) sp.set("posted_within", String(updated.posted_within));
    if (updated.budget_type) sp.set("budget_type", updated.budget_type);
    const qs = sp.toString();
    router.replace(`/dashboard/jobs${qs ? `?${qs}` : ""}`, { scroll: false });
  }, [filterParams, router]);

  const handleClear = useCallback(() => {
    setFilterParams(DEFAULTS);
    router.replace("/dashboard/jobs", { scroll: false });
  }, [router]);

  const swrKey = buildApiUrl(filterParams);

  const { data: jobsData, isLoading } = useSWR(swrKey, fetcher, {
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
    shouldRetryOnError: false,
    errorRetryCount: 0,
  });

  const jobs: Job[] = jobsData?.jobs ?? [];
  const total: number = jobsData?.total ?? 0;

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

  return (
    <div className="flex h-full max-w-7xl mx-auto">
      {/* ── Job list ─────────────────────────────────────────────────────── */}
      <div
        className={`flex-1 p-4 md:p-6 overflow-y-auto transition-all duration-300 ${selectedJobId ? "lg:max-w-md xl:max-w-lg pr-4" : ""
          }`}
      >
        <div className="flex items-center justify-between mb-6 border-b-2 border-border pb-4">
          <div>
            <h1 className="text-3xl font-display font-bold text-white uppercase tracking-tight">
              Job Feed
            </h1>
            <p className="text-slate-400 font-mono text-xs mt-2 uppercase tracking-widest flex items-center gap-2">
              <Zap size={14} className="text-neon-lime" />
              {isLoading ? "Loading..." : `${total} active matches`}
            </p>
          </div>
        </div>

        {/* FilterBar */}
        <FilterBar
          params={filterParams}
          onChange={handleFilterChange}
          onClear={handleClear}
          totalJobs={isLoading ? undefined : jobs.length}
        />

        <div className="space-y-4">
          {isLoading ? (
            Array(5)
              .fill(0)
              .map((_, i) => (
                <div key={i} className="h-32 skeleton border-2 border-border" />
              ))
          ) : jobs.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center py-16 space-y-4"
            >
              <SearchX size={48} className="text-slate-600 mx-auto" />
              {filterParams.min_score || filterParams.budget_type || filterParams.posted_within ? (
                <>
                  <p className="text-slate-400 font-mono text-sm uppercase tracking-widest">
                    No jobs match your filters
                  </p>
                  <button
                    onClick={handleClear}
                    className="text-neon-lime font-mono text-xs font-bold uppercase border border-neon-lime px-4 py-2 hover:bg-neon-lime hover:text-surface-900 transition-colors"
                  >
                    Clear Filters
                  </button>
                </>
              ) : (
                <>
                  <p className="text-white font-semibold">No jobs yet</p>
                  <p className="text-slate-400 text-sm font-mono">
                    Upload your CV, then click <span className="text-neon-lime font-bold">Scrape Now</span> in the bar above to find matching jobs.
                  </p>
                </>
              )}
            </motion.div>
          ) : (
            jobs.map((job, i) => {
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
                    <div className="flex items-center gap-2 shrink-0">
                      {isEasyWin && (
                        <span className="flex items-center gap-1 px-2 py-1 bg-neon-lime text-surface-900 border-2 border-neon-lime font-mono text-xs font-bold uppercase tracking-wider">
                          <Zap size={12} strokeWidth={3} /> EASY WIN
                        </span>
                      )}
                      <button
                        onClick={async (e) => {
                          e.stopPropagation();
                          const isSaved = savedIds.has(job.id);
                          setSavedIds((prev) => {
                            const next = new Set(prev);
                            if (isSaved) next.delete(job.id); else next.add(job.id);
                            return next;
                          });
                          try {
                            if (isSaved) await savedApi.unsave(job.id); else await savedApi.save(job.id);
                          } catch {
                            // revert on error
                            setSavedIds((prev) => {
                              const next = new Set(prev);
                              if (isSaved) next.add(job.id); else next.delete(job.id);
                              return next;
                            });
                          }
                        }}
                        className="p-1 text-slate-500 hover:text-neon-lime transition-colors"
                        title={savedIds.has(job.id) ? "Remove bookmark" : "Bookmark job"}
                      >
                        {savedIds.has(job.id)
                          ? <BookmarkCheck size={16} className="text-neon-lime" strokeWidth={2.5} />
                          : <Bookmark size={16} strokeWidth={2.5} />}
                      </button>
                    </div>
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
                      {job.posted_at
                        ? (() => {
                            const diff = Math.floor((Date.now() - new Date(job.posted_at).getTime()) / 60000);
                            return diff < 60 ? `${diff}m ago` : diff < 1440 ? `${Math.floor(diff/60)}h ago` : `${Math.floor(diff/1440)}d ago`;
                          })()
                        : "—"}
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
              {/* ScoreBadge */}
              <ScoreBadge
                score={selectedJob.score}
              />

              {/* BidRecommendation */}
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

              {/* Phase 3: ProposalPanel */}
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

// ── Required Suspense wrapper for useSearchParams() in Next.js 14 App Router ──
// Without this, Next.js performs a CSR bailout that freezes all interactivity.
export default function JobsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 p-6 space-y-4">
          {Array(5).fill(0).map((_, i) => (
            <div key={i} className="h-32 skeleton border-2 border-border" />
          ))}
        </div>
      }
    >
      <JobsFeed />
    </Suspense>
  );
}
