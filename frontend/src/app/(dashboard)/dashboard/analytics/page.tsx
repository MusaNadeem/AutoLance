"use client";

import { motion } from "framer-motion";

import {
  TrendingUp, DollarSign, Target, Trophy,
  ArrowUp, ArrowDown
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer
} from "recharts";

const winRateData = [
  { month: "Oct", rate: 12, proposals: 8 },
  { month: "Nov", rate: 18, proposals: 11 },
  { month: "Dec", rate: 15, proposals: 9 },
  { month: "Jan", rate: 24, proposals: 15 },
  { month: "Feb", rate: 28, proposals: 18 },
  { month: "Mar", rate: 31, proposals: 22 },
];

const revenueData = [
  { month: "Oct", revenue: 2400 },
  { month: "Nov", revenue: 3800 },
  { month: "Dec", revenue: 2100 },
  { month: "Jan", revenue: 5600 },
  { month: "Feb", revenue: 7200 },
  { month: "Mar", revenue: 9100 },
];

const categoryData = [
  { name: "Python/Backend", value: 48, color: "#6366f1" },
  { name: "React/Frontend", value: 28, color: "#8b5cf6" },
  { name: "Full-Stack", value: 16, color: "#a78bfa" },
  { name: "Other", value: 8, color: "#2d2d4e" },
];

const stats = [
  { label: "Win Rate", value: "31%", change: "+8%", up: true, icon: Trophy },
  { label: "Response Rate", value: "64%", change: "+12%", up: true, icon: TrendingUp },
  { label: "Avg Project Value", value: "$4,200", change: "+$800", up: true, icon: DollarSign },
  { label: "Total Revenue", value: "$30.2K", change: "+$9.1K", up: true, icon: Target },
];

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number }>; label?: string }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface-3 border border-surface-5 rounded-xl px-4 py-3 shadow-xl">
      <p className="text-slate-400 text-xs mb-1">{label}</p>
      {payload.map((p: { name: string; value: number }, i: number) => (
        <p key={i} className="text-white text-sm font-semibold">
          {p.name}: {typeof p.value === "number" && p.name === "revenue" ? `$${p.value.toLocaleString()}` : `${p.value}${p.name === "rate" ? "%" : ""}`}
        </p>
      ))}
    </div>
  );
};

export default function AnalyticsPage() {
  return (
    <div className="p-6 space-y-8 max-w-7xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Analytics</h1>
        <p className="text-slate-400 mt-1">Performance insights across your proposals and wins</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass-card p-5"
          >
            <div className="flex items-center justify-between mb-3">
              <p className="text-slate-400 text-xs font-medium">{stat.label}</p>
              <stat.icon size={16} className="text-brand-400" />
            </div>
            <p className="text-2xl font-bold text-white">{stat.value}</p>
            <div className={`flex items-center gap-1 mt-2 text-xs font-medium ${stat.up ? "text-emerald-400" : "text-red-400"}`}>
              {stat.up ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
              {stat.change} vs last period
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="glass-card p-6">
          <h3 className="font-semibold text-white mb-6">Win Rate Trend</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={winRateData}>
              <defs>
                <linearGradient id="rateGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d2d4e" />
              <XAxis dataKey="month" stroke="#64748b" tick={{ fontSize: 12 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 12 }} unit="%" />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="rate" name="rate" stroke="#6366f1" fill="url(#rateGrad)" strokeWidth={2} dot={{ fill: "#6366f1", r: 4 }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card p-6">
          <h3 className="font-semibold text-white mb-6">Revenue Pipeline</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={revenueData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d2d4e" />
              <XAxis dataKey="month" stroke="#64748b" tick={{ fontSize: 12 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 12 }} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="revenue" name="revenue" radius={[4, 4, 0, 0]}>
                {revenueData.map((_, i) => (
                  <Cell key={i} fill={i === revenueData.length - 1 ? "#6366f1" : "#312e81"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="glass-card p-6">
          <h3 className="font-semibold text-white mb-6">Revenue by Category</h3>
          <div className="flex items-center gap-8">
            <ResponsiveContainer width={160} height={160}>
              <PieChart>
                <Pie data={categoryData} cx={75} cy={75} innerRadius={45} outerRadius={75} dataKey="value" stroke="none">
                  {categoryData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-3 flex-1">
              {categoryData.map((cat) => (
                <div key={cat.name} className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full shrink-0" style={{ background: cat.color }} />
                  <span className="text-sm text-slate-300 flex-1">{cat.name}</span>
                  <span className="text-sm font-semibold text-white">{cat.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="glass-card p-6">
          <h3 className="font-semibold text-white mb-6">Proposal Funnel</h3>
          <div className="space-y-3">
            {[
              { label: "Sent", count: 22, pct: 100, color: "bg-slate-600" },
              { label: "Viewed", count: 18, pct: 82, color: "bg-brand-500" },
              { label: "Replied", count: 14, pct: 64, color: "bg-violet-500" },
              { label: "Interview", count: 8, pct: 36, color: "bg-amber-500" },
              { label: "Won", count: 7, pct: 31, color: "bg-emerald-500" },
            ].map((stage) => (
              <div key={stage.label} className="flex items-center gap-3">
                <div className="w-20 text-sm text-slate-400 shrink-0">{stage.label}</div>
                <div className="flex-1 h-6 bg-surface-4 rounded-lg overflow-hidden">
                  <motion.div
                    className={`h-full ${stage.color} rounded-lg flex items-center px-2`}
                    initial={{ width: 0 }}
                    animate={{ width: `${stage.pct}%` }}
                    transition={{ duration: 0.8, delay: 0.3 }}
                  >
                    <span className="text-white text-xs font-medium">{stage.count}</span>
                  </motion.div>
                </div>
                <div className="w-8 text-xs text-slate-400 text-right shrink-0">{stage.pct}%</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
