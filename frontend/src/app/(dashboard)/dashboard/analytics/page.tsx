"use client";

import { motion } from "framer-motion";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import type { AnalyticsData } from "@/types";
import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from "recharts";
import {
  Database, TrendingUp, Zap, BarChart3,
  Code2, Activity,
} from "lucide-react";

// ── Colour helpers ─────────────────────────────────────────────────────────────

const BUCKET_COLORS: Record<string, string> = {
  "0-25":   "#ff4500",   // red — poor
  "25-50":  "#ff8c00",   // orange — below average
  "50-75":  "#00e5ff",   // neon-cyan — good
  "75-100": "#ccff00",   // neon-lime — excellent
};

const SCORE_LABEL_COLORS: Record<string, string> = {
  "0-25":   "text-neon-pink",
  "25-50":  "text-neon-orange",
  "50-75":  "text-neon-cyan",
  "75-100": "text-neon-lime",
};

// ── Skeleton card ──────────────────────────────────────────────────────────────

function StatCardSkeleton() {
  return <div className="brutal-panel p-6 h-28 skeleton" />;
}

// ── Custom Tooltip ─────────────────────────────────────────────────────────────

function ChartTooltip({ active, payload, label }: {
  active?: boolean;
  payload?: { value: number; name: string }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface-800 border-2 border-border px-3 py-2 font-mono text-xs text-white">
      <p className="text-slate-400 mb-1 uppercase tracking-wider">{label}</p>
      {payload.map((p) => (
        <p key={p.name} className="font-bold">
          {p.name}: <span className="text-neon-lime">{p.value}</span>
        </p>
      ))}
    </div>
  );
}

// ── Demo fallback data ─────────────────────────────────────────────────────────

const DEMO_DATA: AnalyticsData = {
  jobs_scraped_total: 142,
  avg_score: 68,
  score_distribution: [
    { bucket: "0-25",   count: 8 },
    { bucket: "25-50",  count: 31 },
    { bucket: "50-75",  count: 62 },
    { bucket: "75-100", count: 41 },
  ],
  top_skills_in_demand: [
    { skill: "Python",       count: 38 },
    { skill: "React",        count: 34 },
    { skill: "FastAPI",      count: 27 },
    { skill: "TypeScript",   count: 25 },
    { skill: "PostgreSQL",   count: 21 },
    { skill: "Node.js",      count: 19 },
    { skill: "AWS",          count: 16 },
    { skill: "Next.js",      count: 14 },
    { skill: "Docker",       count: 11 },
    { skill: "Redis",        count: 9  },
  ],
  scrape_history: [
    { date: "May 19", jobs_found: 18, jobs_new: 7,  status: "completed" },
    { date: "May 20", jobs_found: 24, jobs_new: 12, status: "completed" },
    { date: "May 21", jobs_found: 15, jobs_new: 5,  status: "completed" },
    { date: "May 22", jobs_found: 31, jobs_new: 18, status: "completed" },
    { date: "May 23", jobs_found: 22, jobs_new: 9,  status: "completed" },
    { date: "May 24", jobs_found: 19, jobs_new: 6,  status: "completed" },
    { date: "May 25", jobs_found: 13, jobs_new: 4,  status: "completed" },
  ],
};

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  const { data: raw, isLoading } = useSWR<AnalyticsData>("/analytics", fetcher, {
    fallbackData: DEMO_DATA,
    revalidateOnFocus: false,
    shouldRetryOnError: false,
    errorRetryCount: 0,
  });

  const data: AnalyticsData = raw ?? DEMO_DATA;

  const totalScored = data.score_distribution.reduce((s, b) => s + b.count, 0);
  const topSkill = data.top_skills_in_demand[0]?.skill ?? "—";
  const lastScrape = data.scrape_history[data.scrape_history.length - 1];

  const summaryCards = [
    {
      id: "stat-jobs-total",
      icon: Database,
      label: "Jobs Scraped",
      value: data.jobs_scraped_total,
      color: "text-neon-lime",
      border: "border-neon-lime",
    },
    {
      id: "stat-avg-score",
      icon: TrendingUp,
      label: "Avg Match Score",
      value: `${data.avg_score}/100`,
      color: "text-neon-cyan",
      border: "border-neon-cyan",
    },
    {
      id: "stat-jobs-scored",
      icon: BarChart3,
      label: "Jobs Scored",
      value: totalScored,
      color: "text-neon-orange",
      border: "border-neon-orange",
    },
    {
      id: "stat-top-skill",
      icon: Code2,
      label: "Top In-Demand Skill",
      value: topSkill,
      color: "text-neon-pink",
      border: "border-neon-pink",
    },
  ];

  return (
    <div className="p-6 space-y-10 max-w-7xl">
      {/* Page header */}
      <div className="border-l-4 border-neon-lime pl-4">
        <h1 className="text-3xl font-display font-bold text-white uppercase tracking-tight">
          Analytics
        </h1>
        <p className="text-slate-400 mt-2 font-mono text-sm uppercase tracking-wider flex items-center gap-2">
          <Activity size={14} className="text-neon-lime" />
          {lastScrape
            ? `Last scrape: ${lastScrape.date} · ${lastScrape.jobs_found} found · ${lastScrape.jobs_new} new`
            : "No scrape data yet"}
        </p>
      </div>

      {/* ── Summary cards ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        {isLoading
          ? Array(4).fill(0).map((_, i) => <StatCardSkeleton key={i} />)
          : summaryCards.map((card, i) => (
              <motion.div
                key={card.label}
                id={card.id}
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07, duration: 0.35, ease: "easeOut" }}
                className={`brutal-panel p-5 border-t-4 ${card.border} group`}
              >
                <div className="flex items-start justify-between mb-4">
                  <p className="text-slate-400 font-mono text-[10px] font-bold uppercase tracking-widest">
                    {card.label}
                  </p>
                  <div className={`w-8 h-8 bg-surface-900 border-2 border-surface-600 flex items-center justify-center ${card.color}`}>
                    <card.icon size={16} strokeWidth={2.5} />
                  </div>
                </div>
                <p className={`text-3xl font-display font-bold ${card.color} group-hover:text-white transition-colors`}>
                  {card.value}
                </p>
              </motion.div>
            ))}
      </div>

      {/* ── Charts row: Score Distribution + Scrape History ───────────────── */}
      <div className="grid lg:grid-cols-2 gap-8">
        {/* Score Distribution Histogram */}
        <motion.div
          id="chart-score-distribution"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.4 }}
          className="brutal-panel p-6"
        >
          <h2 className="font-display font-bold text-white uppercase tracking-wider mb-6 flex items-center gap-3">
            <Zap size={18} strokeWidth={2.5} className="text-neon-lime" />
            Score Distribution
          </h2>
          {isLoading ? (
            <div className="h-48 skeleton" />
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={data.score_distribution} barCategoryGap="20%">
                <CartesianGrid strokeDasharray="3 3" stroke="#2e2e2e" vertical={false} />
                <XAxis
                  dataKey="bucket"
                  tick={{ fill: "#64748b", fontFamily: "monospace", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "#64748b", fontFamily: "monospace", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  width={30}
                />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="count" name="Jobs" radius={0}>
                  {data.score_distribution.map((entry) => (
                    <Cell key={entry.bucket} fill={BUCKET_COLORS[entry.bucket]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
          <div className="flex flex-wrap gap-3 mt-4">
            {data.score_distribution.map((b) => (
              <div key={b.bucket} className="flex items-center gap-1.5">
                <div className="w-3 h-3" style={{ backgroundColor: BUCKET_COLORS[b.bucket] }} />
                <span className={`font-mono text-[10px] font-bold uppercase ${SCORE_LABEL_COLORS[b.bucket]}`}>
                  {b.bucket} · {b.count}
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Scrape History Line Chart */}
        <motion.div
          id="chart-scrape-history"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.4 }}
          className="brutal-panel p-6"
        >
          <h2 className="font-display font-bold text-white uppercase tracking-wider mb-6 flex items-center gap-3">
            <Activity size={18} strokeWidth={2.5} className="text-neon-cyan" />
            Scrape History — Last 7 Runs
          </h2>
          {isLoading ? (
            <div className="h-48 skeleton" />
          ) : data.scrape_history.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-slate-600 font-mono text-sm">
              No scrape runs yet
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={data.scrape_history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2e2e2e" vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#64748b", fontFamily: "monospace", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "#64748b", fontFamily: "monospace", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  width={30}
                />
                <Tooltip content={<ChartTooltip />} />
                <Line
                  type="monotone"
                  dataKey="jobs_found"
                  name="Found"
                  stroke="#00e5ff"
                  strokeWidth={2}
                  dot={{ fill: "#00e5ff", r: 3 }}
                  activeDot={{ r: 5 }}
                />
                <Line
                  type="monotone"
                  dataKey="jobs_new"
                  name="New"
                  stroke="#ccff00"
                  strokeWidth={2}
                  dot={{ fill: "#ccff00", r: 3 }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
          <div className="flex gap-6 mt-4">
            <div className="flex items-center gap-1.5">
              <div className="w-4 h-0.5 bg-neon-cyan" />
              <span className="font-mono text-[10px] font-bold uppercase text-neon-cyan">Jobs Found</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-4 h-0.5 bg-neon-lime" />
              <span className="font-mono text-[10px] font-bold uppercase text-neon-lime">New Jobs</span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* ── Top Skills in Demand ───────────────────────────────────────────── */}
      <motion.div
        id="chart-top-skills"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.4 }}
        className="brutal-panel p-6"
      >
        <h2 className="font-display font-bold text-white uppercase tracking-wider mb-6 flex items-center gap-3">
          <Code2 size={18} strokeWidth={2.5} className="text-neon-pink" />
          Top 10 Skills in Demand
        </h2>
        {isLoading ? (
          <div className="h-64 skeleton" />
        ) : data.top_skills_in_demand.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-slate-600 font-mono text-sm">
            No skill data yet
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart
              data={data.top_skills_in_demand}
              layout="vertical"
              barCategoryGap="18%"
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#2e2e2e" horizontal={false} />
              <XAxis
                type="number"
                tick={{ fill: "#64748b", fontFamily: "monospace", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="skill"
                width={90}
                tick={{ fill: "#e2e8f0", fontFamily: "monospace", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<ChartTooltip />} />
              <Bar dataKey="count" name="Jobs" fill="#ccff00" radius={0} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </motion.div>
    </div>
  );
}
