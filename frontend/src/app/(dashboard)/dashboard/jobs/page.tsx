/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import {
  Filter, Clock, Users, DollarSign,
  Zap, Shield, ShieldAlert, ShieldX, X,
  Sparkles
} from "lucide-react";

const tierConfig: Record<string, { label: string; badge: string; icon: React.ComponentType<{ size?: number; strokeWidth?: number }> }> = {
  high: { label: "High Quality", badge: "badge-high", icon: Shield },
  medium: { label: "Medium", badge: "badge-medium", icon: Shield },
  risky: { label: "Risky", badge: "badge-risky", icon: ShieldAlert },
  avoid: { label: "Avoid", badge: "badge-avoid", icon: ShieldX },
};

function ScoreBar({ score }: { score: number }) {
  const color = score >= 85 ? "bg-neon-lime" : score >= 70 ? "bg-neon-cyan" : score >= 50 ? "bg-neon-orange" : "bg-neon-pink";
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-3 bg-surface-800 border-2 border-border overflow-hidden">
        <motion.div
          className={`h-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 }}
        />
      </div>
      <span className={`text-sm font-bold font-mono w-8 text-right ${color.replace("bg-", "text-")}`}>{score}</span>
    </div>
  );
}

export default function JobsPage() {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [coverLetter, setCoverLetter] = useState<string | null>(null);

  const demoJobs = [
    {
      id: "demo-1",
      title: "FastAPI Backend — Real-Time Analytics",
      description: "Build a high-throughput FastAPI backend with Redis caching and Postgres analytics queries.",
      budget_type: "hourly",
      budget_min: 75,
      budget_max: 110,
      proposal_count: 6,
      proposal_tier: "low",
      required_skills: JSON.stringify(["FastAPI", "PostgreSQL", "Redis"]),
      score: 85,
    },
    {
      id: "demo-2",
      title: "React Native Developer for FinTech App",
      description: "Implement core flows for a fintech mobile app and integrate with REST APIs.",
      budget_type: "fixed",
      budget_min: 2500,
      budget_max: 4500,
      proposal_count: 14,
      proposal_tier: "medium",
      required_skills: JSON.stringify(["React Native", "TypeScript", "API Integration"]),
      score: 87,
    },
    {
      id: "demo-3",
      title: "Python ML Engineer — Healthcare AI",
      description: "Train and deploy a small NLP model, build evaluation, and integrate into an API.",
      budget_type: "hourly",
      budget_min: 90,
      budget_max: 140,
      proposal_count: 9,
      proposal_tier: "low",
      required_skills: JSON.stringify(["Python", "ML", "NLP"]),
      score: 91,
    },
  ];

  const { data: jobsData, isLoading } = useSWR("/jobs", fetcher, {
    fallbackData: {
      jobs: demoJobs,
    },
  });
  const apiJobs = jobsData?.jobs || [];
  const jobs = apiJobs.length ? apiJobs : demoJobs;

  const { data: jobDetails } = useSWR(selectedJobId ? `/jobs/${selectedJobId}` : null, fetcher);
  const selectedJob = jobDetails || jobs.find((j: any) => j.id === selectedJobId);

  const handleGenerate = () => {
    setGenerating(true);
    setTimeout(() => {
      setGenerating(false);
      setCoverLetter(
        `I noticed you're building a high-throughput data pipeline — this is exactly the kind of challenge I've spent the last 3 years optimizing.\n\nA few specifics I'd bring:\n• Scalable architecture\n• High performance execution\n• Reliable delivery\n\nI'd love to dig into your current bottlenecks.\n\nBest,\nAlex`
      );
    }, 2000);
  };

  return (
    <div className="flex h-full max-w-7xl mx-auto">
      <div className={`flex-1 p-4 md:p-6 overflow-y-auto transition-all duration-300 ${selectedJobId ? "lg:max-w-md xl:max-w-lg pr-4" : ""}`}>
        <div className="flex items-center justify-between mb-8 border-b-2 border-border pb-4">
          <div>
            <h1 className="text-3xl font-display font-bold text-white uppercase tracking-tight">Job Feed</h1>
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
            Array(5).fill(0).map((_, i) => <div key={i} className="h-32 skeleton border-2 border-border" />)
          ) : (
            jobs.map((job: any, i: number) => {
              const score = (job.score as number) || Math.floor(Math.random() * 30 + 65);
              const isEasyWin = score > 85;
              const clientTier = job.proposal_tier === "low" ? "high" : "medium";

              return (
                <motion.div
                  key={job.id}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05, duration: 0.25, ease: "easeOut" }}
                  onClick={() => { setSelectedJobId(job.id); setCoverLetter(null); }}
                  className={`brutal-panel p-5 cursor-pointer transition-all duration-150 ${
                    selectedJobId === job.id
                      ? "border-neon-lime translate-x-2"
                      : ""
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

                  <ScoreBar score={score} />

                  <div className="flex flex-wrap gap-4 mt-5 font-mono text-xs font-bold text-slate-400 uppercase tracking-wide">
                    <span className="flex items-center gap-1 text-white"><DollarSign size={14} strokeWidth={2.5} />
                      {job.budget_type === "fixed" ? `$${job.budget_min || 0} - $${job.budget_max || 0}` : `$${job.budget_min || 0}/hr`}
                    </span>
                    <span className="flex items-center gap-1"><Users size={14} strokeWidth={2.5} />{job.proposal_count || 0} PROPOSALS</span>
                    <span className="flex items-center gap-1"><Clock size={14} strokeWidth={2.5} />2h AGO</span>
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

      <AnimatePresence>
        {selectedJobId && selectedJob && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="hidden lg:flex w-[500px] xl:w-[600px] border-l-2 border-border flex-col h-full bg-surface-900"
          >
            <div className="p-6 border-b-2 border-border flex items-start justify-between bg-surface-800">
              <h2 className="text-lg font-display font-bold text-white leading-snug flex-1 pr-6 uppercase tracking-wide">
                {selectedJob.title}
              </h2>
              <button onClick={() => setSelectedJobId(null)} className="text-slate-400 hover:text-neon-pink transition-colors">
                <X size={24} strokeWidth={2.5} />
              </button>
            </div>

            <div className="p-6 space-y-8 flex-1 overflow-y-auto">
              <div className="brutal-panel p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-display font-bold text-white uppercase tracking-wide">{(selectedJob.title as string) || "React Native Architect Needed"}</h3>
                  <span className="text-4xl font-bold font-mono text-neon-lime">{selectedJob.score || 88}</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="border-2 border-border bg-surface-900 p-3">
                    <div className="text-slate-400 font-mono text-xs font-bold uppercase tracking-wider mb-1">Win Probability</div>
                    <div className="font-bold text-white font-mono text-lg">{(0.68 * 100).toFixed(0)}%</div>
                  </div>
                  <div className="border-2 border-border bg-surface-900 p-3">
                    <div className="text-slate-400 font-mono text-xs font-bold uppercase tracking-wider mb-1">Competition</div>
                    <div className="font-bold text-white font-mono text-lg uppercase">{selectedJob.proposal_tier || "Low"}</div>
                  </div>
                </div>
              </div>

              <div className="brutal-panel p-5">
                <h3 className="font-display font-bold text-white mb-4 uppercase tracking-wider flex items-center gap-3">
                  <Shield size={18} strokeWidth={2.5} className="text-neon-cyan" />
                  Client Quality
                  <span className={`ml-auto ${tierConfig["high"].badge}`}>
                    {tierConfig["high"].label}
                  </span>
                </h3>
                <div className="grid grid-cols-3 gap-3 text-center mb-4">
                  <div className="border-2 border-border bg-surface-900 p-2">
                    <div className="text-slate-400 font-mono text-[10px] font-bold uppercase mb-1">Total Spent</div>
                    <div className="font-bold font-mono text-white text-sm">{selectedJob.client?.total_spent || "$10K+"}</div>
                  </div>
                  <div className="border-2 border-border bg-surface-900 p-2">
                    {(selectedJob.client as any)?.paymentVerified && <Shield size={14} className="text-emerald-400" />}
                    <span className="text-slate-400">{(selectedJob.client as any)?.location || "United States"}</span>
                    <span className="text-slate-600">•</span>
                    <span className="text-slate-400">{(selectedJob.client as any)?.history || "$10k+ spent"}</span>
                    <div className="font-bold font-mono text-white text-sm">{selectedJob.client?.hire_rate || "75"}%</div>
                  </div>
                  <div className="border-2 border-border bg-surface-900 p-2">
                    <div className="text-slate-400 font-mono text-[10px] font-bold uppercase mb-1">Rating</div>
                    <div className="font-bold font-mono text-white text-sm">⭐ {selectedJob.client?.average_rating || "4.8"}</div>
                  </div>
                </div>
              </div>

              <div className="border-l-4 border-neon-cyan pl-4">
                <h3 className="font-display font-bold text-white mb-3 uppercase tracking-wider">Job Description</h3>
                <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
                  {selectedJob.description}
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                {((selectedJob.required_skills && typeof selectedJob.required_skills === 'string')
                    ? JSON.parse(selectedJob.required_skills)
                    : ["React", "FastAPI"]).map((s: string) => (
                  <span key={s} className="px-3 py-1 bg-surface-800 border-2 border-border text-slate-300 font-mono text-xs font-bold uppercase">
                    {s}
                  </span>
                ))}
              </div>

              {!coverLetter ? (
                <button onClick={handleGenerate} disabled={generating} className="btn-primary w-full flex items-center justify-center gap-3 py-4 mt-8">
                  {generating ? (
                    <><Zap size={18} className="animate-pulse" strokeWidth={2.5} /> GENERATING...</>
                  ) : (
                    <><Sparkles size={18} strokeWidth={2.5} /> GENERATE AI COVER LETTER</>
                  )}
                </button>
              ) : (
                <div className="mt-8 border-2 border-neon-lime p-5 bg-surface-800 relative">
                  {(selectedJob.score as number) > 85 && <div className="absolute -top-3 -right-3 w-8 h-8 bg-neon-pink border-2 border-surface-900 rounded-full flex items-center justify-center shadow-[2px_2px_0px_0px_rgba(46,46,46,1)] animate-bounce z-10"><Zap size={14} className="text-surface-900 fill-surface-900" /></div>}
                  <h3 className="font-display font-bold text-white mb-4 uppercase tracking-wider flex items-center gap-3">
                    <Sparkles size={18} className="text-neon-lime" strokeWidth={2.5} />
                    AI Cover Letter
                  </h3>
                  <div className="bg-surface-900 border-2 border-border p-4 mb-4">
                    <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap font-mono">
                      {coverLetter}
                    </p>
                  </div>
                  <div className="flex gap-4">
                    <button className="btn-primary flex-1">COPY & APPLY</button>
                    <button onClick={handleGenerate} className="btn-ghost">REGENERATE</button>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
