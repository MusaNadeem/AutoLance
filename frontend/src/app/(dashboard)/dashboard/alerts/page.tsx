"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Bell, Slack, Mail, Smartphone, Save, Check, Zap } from "lucide-react";
import useSWR from "swr";
import { alerts, fetcher } from "@/lib/api";

type Channel = "email" | "push" | "slack";

type AlertConfigApi = {
  min_match_score: number;
  max_proposal_count: number;
  max_hours_since_posted: number;
  min_client_quality_score: number;
  notify_slack: boolean;
  notify_email: boolean;
  notify_push: boolean;
  is_active?: boolean;
};

type AlertConfigApiMessage = { message: string };

type AlertEventApi = {
  id: string;
  job_id: string;
  job_title?: string | null;
  match_score?: number | null;
  trigger_reason?: string | null;
  channel?: Channel | string | null;
  sent_at?: string | null;
  read_at?: string | null;
  is_actioned?: boolean | null;
};

type AlertsUiConfig = {
  minScore: number;
  maxProposals: number;
  maxHours: number;
  minClientScore: number;
  slack: boolean;
  email: boolean;
  push: boolean;
  slackWebhook: string;
};

function timeAgo(input: string | Date) {
  const date = typeof input === "string" ? new Date(input) : input;
  const diffMs = Date.now() - date.getTime();
  const diffMinutes = Math.max(0, Math.floor(diffMs / 60000));
  if (diffMinutes < 60) return `${diffMinutes} min ago`;
  const hours = Math.floor(diffMinutes / 60);
  return `${hours} hrs ago`;
}

export default function AlertsPage() {
  const demoEvents: AlertEventApi[] = useMemo(
    () => [
      { id: "demo-1", job_id: "demo-1", job_title: "Senior Python Developer — FastAPI + Celery", match_score: 94, sent_at: new Date(Date.now() - 2 * 60000).toISOString(), channel: "email", is_actioned: false },
      { id: "demo-2", job_id: "demo-2", job_title: "React Native Developer for FinTech App", match_score: 88, sent_at: new Date(Date.now() - 18 * 60000).toISOString(), channel: "slack", is_actioned: true },
      { id: "demo-3", job_id: "demo-3", job_title: "FastAPI Backend — Real-Time Analytics Platform", match_score: 85, sent_at: new Date(Date.now() - 41 * 60000).toISOString(), channel: "email", is_actioned: true },
      { id: "demo-4", job_id: "demo-4", job_title: "Python ML Engineer — Healthcare AI Startup", match_score: 91, sent_at: new Date(Date.now() - 72 * 60000).toISOString(), channel: "push", is_actioned: true },
      { id: "demo-5", job_id: "demo-5", job_title: "TypeScript Full-Stack Developer — B2B SaaS", match_score: 87, sent_at: new Date(Date.now() - 150 * 60000).toISOString(), channel: "email", is_actioned: false },
    ],
    []
  );

  const { data: configData } = useSWR<AlertConfigApi | AlertConfigApiMessage>("/alerts/config", fetcher);
  const { data: eventsData, isLoading: eventsLoading } = useSWR<AlertEventApi[]>("/alerts/events", fetcher, {
    fallbackData: demoEvents,
  });

  const apiEvents = eventsData ?? [];
  const recentAlerts = apiEvents.length ? apiEvents : demoEvents;

  const [config, setConfig] = useState<AlertsUiConfig>({
    minScore: 85,
    maxProposals: 10,
    maxHours: 2,
    minClientScore: 60,
    slack: false,
    email: true,
    push: true,
    slackWebhook: "",
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!configData) return;
    if ("message" in configData) return;
    const c = configData;
    setConfig((prev) => ({
      ...prev,
      minScore: Number(c.min_match_score ?? prev.minScore),
      maxProposals: Number(c.max_proposal_count ?? prev.maxProposals),
      maxHours: Number(c.max_hours_since_posted ?? prev.maxHours),
      minClientScore: Number(c.min_client_quality_score ?? prev.minClientScore),
      slack: Boolean(c.notify_slack ?? prev.slack),
      email: Boolean(c.notify_email ?? prev.email),
      push: Boolean(c.notify_push ?? prev.push),
    }));
  }, [configData]);

  const handleSave = async () => {
    await alerts.updateConfig({
      min_match_score: config.minScore,
      max_proposal_count: config.maxProposals,
      max_hours_since_posted: config.maxHours,
      min_client_quality_score: config.minClientScore,
      notify_slack: config.slack,
      notify_email: config.email,
      notify_push: config.push,
      slack_webhook_url: config.slackWebhook || null,
    });

    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const toggleChannel = (key: Channel) => {
    setConfig(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const channelIcon = (ch?: string | null) => ch === "email" ? "📧" : ch === "slack" ? "💬" : "📱";

  return (
    <div className="p-6 space-y-8 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Alert Center</h1>
        <p className="text-slate-400 mt-1">Configure thresholds and view notification history</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        <div className="glass-card p-6 space-y-6">
          <h2 className="font-semibold text-white flex items-center gap-2">
            <Bell size={16} className="text-brand-400" /> Alert Thresholds
          </h2>

          <div className="space-y-5">
            <div>
              <div className="flex justify-between mb-2">
                <label className="text-sm text-slate-300">Minimum Match Score</label>
                <span className="text-brand-400 font-bold font-mono">{config.minScore}</span>
              </div>
              <input
                type="range" min={50} max={99} value={config.minScore}
                onChange={(e) => setConfig({ ...config, minScore: +e.target.value })}
                className="w-full accent-brand-500 h-1.5 rounded-full bg-surface-4"
              />
              <div className="flex justify-between text-xs text-slate-500 mt-1">
                <span>50</span><span>99</span>
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-2">
                <label className="text-sm text-slate-300">Max Proposals on Job</label>
                <span className="text-violet-400 font-bold font-mono">{config.maxProposals}</span>
              </div>
              <input
                type="range" min={1} max={50} value={config.maxProposals}
                onChange={(e) => setConfig({ ...config, maxProposals: +e.target.value })}
                className="w-full accent-violet-500 h-1.5 rounded-full bg-surface-4"
              />
            </div>

            <div>
              <div className="flex justify-between mb-2">
                <label className="text-sm text-slate-300">Max Hours Since Posted</label>
                <span className="text-amber-400 font-bold font-mono">{config.maxHours}h</span>
              </div>
              <input
                type="range" min={1} max={24} value={config.maxHours}
                onChange={(e) => setConfig({ ...config, maxHours: +e.target.value })}
                className="w-full accent-amber-500 h-1.5 rounded-full bg-surface-4"
              />
            </div>

            <div>
              <div className="flex justify-between mb-2">
                <label className="text-sm text-slate-300">Min Client Quality Score</label>
                <span className="text-emerald-400 font-bold font-mono">{config.minClientScore}</span>
              </div>
              <input
                type="range" min={0} max={100} value={config.minClientScore}
                onChange={(e) => setConfig({ ...config, minClientScore: +e.target.value })}
                className="w-full accent-emerald-500 h-1.5 rounded-full bg-surface-4"
              />
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-white mb-3">Notification Channels</h3>
            <div className="space-y-2">
              {[
                { key: "email", icon: Mail, label: "Email Alerts", color: "text-blue-400" },
                { key: "push", icon: Smartphone, label: "Push Notifications", color: "text-violet-400" },
                { key: "slack", icon: Slack, label: "Slack Webhook", color: "text-emerald-400" },
              ].map((ch) => (
                <div key={ch.key} className="flex items-center justify-between p-3 rounded-xl bg-surface-4 border border-surface-5">
                  <div className="flex items-center gap-3">
                    <ch.icon size={16} className={ch.color} />
                    <span className="text-sm text-slate-300">{ch.label}</span>
                  </div>
                  <button
                    onClick={() => toggleChannel(ch.key as "email" | "push" | "slack")}
                    className={`w-10 h-5 rounded-full transition-colors duration-200 relative ${config[ch.key as "email" | "push" | "slack"] ? "bg-brand-500" : "bg-surface-5"}`}
                  >
                    <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform duration-200 ${config[ch.key as "email" | "push" | "slack"] ? "left-5" : "left-0.5"}`} />
                  </button>
                </div>
              ))}
            </div>

            {config.slack && (
              <motion.input
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                type="text"
                placeholder="https://hooks.slack.com/services/..."
                value={config.slackWebhook}
                onChange={(e) => setConfig({ ...config, slackWebhook: e.target.value })}
                className="mt-2 w-full bg-surface-4 border border-surface-5 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
              />
            )}
          </div>

          <button onClick={handleSave} className="btn-primary w-full flex items-center justify-center gap-2">
            {saved ? <><Check size={16} /> Saved!</> : <><Save size={16} /> Save Configuration</>}
          </button>
        </div>

        <div className="glass-card p-6">
          <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
            <Zap size={16} className="text-amber-400" /> Recent Alerts
          </h2>
          <div className="space-y-3">
            {eventsLoading ? (
              <div className="h-40 skeleton rounded-xl border border-surface-5" />
            ) : recentAlerts.map((alert, i) => (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.08 }}
                className={`p-3.5 rounded-xl border transition-all ${alert.is_actioned ? "border-surface-5 bg-surface-4/30 opacity-60" : "border-brand-500/20 bg-brand-500/5"}`}
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-brand-500/10 border border-brand-500/20 flex items-center justify-center shrink-0">
                    <span className="text-brand-300 font-bold text-sm font-mono">{alert.match_score ?? "—"}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white leading-snug">{alert.job_title || `Job ${String(alert.job_id || "").slice(0, 8)}`}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-slate-500">{alert.sent_at ? timeAgo(alert.sent_at) : ""}</span>
                      <span className="text-xs text-slate-600">·</span>
                      <span className="text-xs text-slate-500">{channelIcon(alert.channel)} {alert.channel ?? "email"}</span>
                      {!alert.is_actioned && (
                        <span className="ml-auto px-2 py-0.5 rounded-full bg-brand-500/15 text-brand-300 text-xs border border-brand-500/20">New</span>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
