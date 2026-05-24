/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { motion } from "framer-motion";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import {
  TrendingUp, Target, Zap, Trophy, ArrowUp, ArrowRight,
  Clock, Users, DollarSign, Activity
} from "lucide-react";

const statsConfig = [
  { key: "active_matches", label: "ACTIVE MATCHES", change: "+12", icon: Target, color: "text-neon-lime" },
  { key: "win_rate", label: "WIN RATE", change: "+8%", icon: Trophy, color: "text-neon-cyan" },
  { key: "proposals_sent", label: "PROPOSALS SENT", change: "+3", icon: TrendingUp, color: "text-neon-pink" },
  { key: "revenue", label: "PIPELINE VALUE", change: "+$2.1K", icon: DollarSign, color: "text-neon-orange" },
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

export default function DashboardPage() {
  const demoJobs = [
    {
      id: "demo-1",
      title: "FastAPI Backend — Real-Time Analytics",
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
      budget_type: "hourly",
      budget_min: 90,
      budget_max: 140,
      proposal_count: 9,
      proposal_tier: "low",
      required_skills: JSON.stringify(["Python", "ML", "NLP"]),
      score: 91,
    },
  ];

  const demoAlertEvents = [
    { id: "demo-a1", job_id: "demo-1", job_title: "Python ML Engineer — Healthcare AI", match_score: 91, sent_at: new Date(Date.now() - 2 * 60000).toISOString(), channel: "email", is_actioned: false },
    { id: "demo-a2", job_id: "demo-2", job_title: "React Native Developer for FinTech App", match_score: 87, sent_at: new Date(Date.now() - 18 * 60000).toISOString(), channel: "slack", is_actioned: true },
    { id: "demo-a3", job_id: "demo-3", job_title: "FastAPI Backend — Real-Time Analytics", match_score: 85, sent_at: new Date(Date.now() - 41 * 60000).toISOString(), channel: "email", is_actioned: true },
  ];

  const timeAgo = (input: string | Date) => {
    const date = typeof input === "string" ? new Date(input) : input;
    const diffMs = Date.now() - date.getTime();
    const diffMinutes = Math.max(0, Math.floor(diffMs / 60000));
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const hours = Math.floor(diffMinutes / 60);
    return `${hours}h ago`;
  };

  const { data: jobsData, isLoading: jobsLoading } = useSWR("/jobs?limit=5", fetcher, {
    fallbackData: {
      jobs: demoJobs,
    },
  });
  const { data: statsData, isLoading: statsLoading } = useSWR("/proposals/analytics", fetcher, {
    fallbackData: { active_matches: 47, win_rate: "31%", proposals_sent: 18, revenue: "$12.4K" }
  });

  const { data: alertEventsData } = useSWR("/alerts/events", fetcher, {
    fallbackData: demoAlertEvents,
  });
  const apiAlertEvents = Array.isArray(alertEventsData) ? alertEventsData : [];
  const recentAlerts = apiAlertEvents.length ? apiAlertEvents : demoAlertEvents;

  const apiJobs = jobsData?.jobs || [];
  const jobs = apiJobs.length ? apiJobs : demoJobs;

  return (
    <div className="p-6 space-y-8 max-w-7xl">
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
                  {statsLoading ? "..." : statsData[stat.key]}
                </p>
              </div>
              <div className={`w-10 h-10 border-2 border-surface-600 bg-surface-900 flex items-center justify-center ${stat.color} group-hover:border-neon-lime transition-colors`}>
                <stat.icon size={20} strokeWidth={2.5} />
              </div>
            </div>
            <div className="flex items-center gap-1 mt-4 text-neon-lime font-mono text-xs font-bold">
              <ArrowUp size={14} strokeWidth={3} />
              {stat.change} THIS WEEK
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
          ) : (
            jobs.slice(0, 3).map((job: any, i: number) => (
              <motion.div
                key={job.id}
                initial={{ opacity: 0, x: -24 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 + 0.2, duration: 0.3, ease: "easeOut" }}
                className="brutal-panel p-5 cursor-pointer group"
              >
                <div className="flex items-start gap-5">
                  <ScoreRing score={(job.score as number) || Math.floor(Math.random() * 20 + 80)} />

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="font-display font-bold text-lg text-white group-hover:text-neon-lime transition-colors truncate">
                        {job.title}
                      </h3>
                      <div className="flex items-center gap-2 shrink-0">
                        {job.score > 90 && (
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
                      {(job.required_skills ? JSON.parse(job.required_skills as string) : ["React", "FastAPI"]).slice(0, 3).map((skill: string) => (
                        <span key={skill} className="px-2 py-1 border-2 border-surface-600 bg-surface-900 text-slate-300 font-mono text-xs font-bold">
                          {skill}
                        </span>
                      ))}
                      <button className="ml-auto btn-primary text-xs py-2 px-4 opacity-0 group-hover:opacity-100 transition-opacity">
                        Generate Cover Letter
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))
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
            {recentAlerts.map((alert: any) => (
              <div key={alert.id} className="flex items-center gap-4 p-3 border-2 border-transparent hover:border-neon-pink bg-surface-900 transition-colors cursor-pointer">
                <div className="w-12 h-12 bg-surface-800 border-2 border-border flex items-center justify-center shrink-0">
                  <span className="text-neon-pink font-bold font-mono text-lg">{alert.match_score ?? "—"}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-bold text-white truncate">{alert.job_title || `Job ${String(alert.job_id || "").slice(0, 8)}`}</p>
                  <p className="text-xs font-mono text-slate-500 uppercase mt-1">{alert.sent_at ? timeAgo(alert.sent_at) : ""}</p>
                </div>
                <ArrowRight size={18} className="text-slate-500 shrink-0" strokeWidth={2.5} />
              </div>
            ))}
          </div>
        </div>

        {/* Proposal status */}
        <div className="brutal-panel p-6">
          <h3 className="font-display font-bold text-white mb-6 uppercase tracking-wide">Proposal Pipeline</h3>
          <div className="space-y-4">
            {[
              { status: "Interview", label: "Cloud Architect Role", value: "$5,500", color: "text-neon-cyan border-neon-cyan" },
              { status: "Replied", label: "React Dashboard Project", value: "$2,200", color: "text-neon-pink border-neon-pink" },
              { status: "Sent", label: "FastAPI Microservices", value: "$3,800", color: "text-neon-orange border-neon-orange" },
              { status: "Won 🎉", label: "Python Data Pipeline", value: "$4,000", color: "text-neon-lime border-neon-lime" },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-4 p-2">
                <span className={`text-xs px-2 py-1 border-2 font-mono font-bold uppercase tracking-wider w-24 text-center shrink-0 ${item.color}`}>
                  {item.status}
                </span>
                <span className="text-sm font-bold text-slate-300 flex-1 truncate">{item.label}</span>
                <span className="text-sm font-mono font-bold text-white shrink-0">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
