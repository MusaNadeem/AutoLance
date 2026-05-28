"use client";

import useSWR, { mutate } from "swr";
import { useState } from "react";
import { motion } from "framer-motion";
import { Bookmark, DollarSign, Users, Clock, Loader2, BookmarkX } from "lucide-react";
import { saved as savedApi } from "@/lib/api";
import type { Job } from "@/types";

export default function SavedJobsPage() {
  const [removingId, setRemovingId] = useState<string | null>(null);

  const { data: jobs, isLoading } = useSWR<Job[]>(
    "/saved-jobs",
    () => savedApi.list().then((r) => r.data),
    { revalidateOnFocus: false }
  );

  const handleUnsave = async (id: string) => {
    setRemovingId(id);
    try {
      await savedApi.unsave(id);
      mutate("/saved-jobs");
    } finally {
      setRemovingId(null);
    }
  };

  const allJobs = jobs ?? [];
  const isEmpty = !isLoading && allJobs.length === 0;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Bookmark size={22} className="text-neon-lime" strokeWidth={2.5} />
          Saved Jobs
        </h1>
        <p className="text-slate-400 mt-1">Jobs you&apos;ve bookmarked for later</p>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-24">
          <Loader2 size={28} className="animate-spin text-brand-400" />
        </div>
      )}

      {isEmpty && (
        <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
          <div className="w-16 h-16 rounded-2xl bg-surface-4 border border-surface-5 flex items-center justify-center">
            <Bookmark size={28} className="text-slate-500" strokeWidth={2} />
          </div>
          <div>
            <p className="text-white font-semibold text-lg">No saved jobs</p>
            <p className="text-slate-400 text-sm mt-1">
              Bookmark jobs from the{" "}
              <a href="/dashboard/jobs" className="text-brand-400 hover:underline">jobs feed</a>
              {" "}to find them here.
            </p>
          </div>
        </div>
      )}

      <div className="grid gap-4">
        {allJobs.map((job, i) => {
          const scoreVal = job.score?.overall != null ? Math.round(job.score.overall * 100) : null;
          return (
            <motion.div
              key={job.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: removingId === job.id ? 0.3 : 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              className="brutal-panel p-5 flex items-start gap-4"
            >
              {/* Score ring */}
              {scoreVal != null && (
                <div className={`w-12 h-12 shrink-0 rounded-xl border-2 flex items-center justify-center font-mono font-bold text-sm ${
                  scoreVal >= 85 ? "border-neon-lime text-neon-lime bg-neon-lime/10" :
                  scoreVal >= 70 ? "border-neon-cyan text-neon-cyan bg-neon-cyan/10" :
                  "border-neon-orange text-neon-orange bg-neon-orange/10"
                }`}>
                  {scoreVal}
                </div>
              )}

              <div className="flex-1 min-w-0">
                <h3 className="font-display font-bold text-white text-sm uppercase tracking-wide leading-snug mb-1 line-clamp-2">
                  {job.title}
                </h3>
                <div className="flex flex-wrap gap-3 text-xs font-mono text-slate-400 mt-2">
                  <span className="flex items-center gap-1">
                    <DollarSign size={12} />
                    {job.budget_type === "fixed"
                      ? `$${job.budget_min ?? 0}–$${job.budget_max ?? 0}`
                      : `$${job.hourly_rate_min ?? 0}/hr`}
                  </span>
                  <span className="flex items-center gap-1">
                    <Users size={12} />
                    {job.proposal_count} proposals
                  </span>
                  {job.posted_at && (
                    <span className="flex items-center gap-1">
                      <Clock size={12} />
                      {new Date(job.posted_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
                <div className="flex gap-2 mt-3">
                  {(job.required_skills ?? []).slice(0, 4).map((s) => (
                    <span key={s} className="px-2 py-0.5 bg-surface-4 border border-surface-5 text-slate-300 text-xs font-mono rounded-lg">
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex flex-col gap-2 shrink-0">
                {job.url && (
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1.5 border-2 border-neon-cyan text-neon-cyan font-mono text-xs uppercase tracking-widest hover:bg-neon-cyan/10 transition-colors"
                  >
                    View
                  </a>
                )}
                <button
                  onClick={() => handleUnsave(job.id)}
                  disabled={removingId === job.id}
                  className="px-3 py-1.5 border-2 border-border text-slate-500 font-mono text-xs uppercase tracking-widest hover:border-neon-pink hover:text-neon-pink transition-colors flex items-center gap-1 disabled:opacity-40"
                >
                  <BookmarkX size={12} /> Remove
                </button>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
