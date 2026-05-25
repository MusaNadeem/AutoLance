"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { motion, AnimatePresence } from "framer-motion";
import { Bell, CheckCheck, BellOff, ExternalLink, Filter } from "lucide-react";
import { notifications } from "@/lib/api";
import type { NotificationsResponse, Notification } from "@/types";

// ── Helpers ───────────────────────────────────────────────────────────────────

function relativeTime(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60)    return `${diff}s ago`;
  if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function scoreColor(score: number): { text: string; bg: string; border: string } {
  if (score >= 0.85) return { text: "text-neon-lime",   bg: "bg-neon-lime/10",   border: "border-neon-lime" };
  if (score >= 0.70) return { text: "text-neon-cyan",   bg: "bg-neon-cyan/10",   border: "border-neon-cyan" };
  if (score >= 0.50) return { text: "text-neon-orange", bg: "bg-neon-orange/10", border: "border-neon-orange" };
  return              { text: "text-neon-pink",   bg: "bg-neon-pink/10",   border: "border-neon-pink" };
}

const fetcher = () => notifications.list().then((r) => r.data);

// ── Page ──────────────────────────────────────────────────────────────────────

type Filter = "all" | "unread" | "read";

export default function AlertsPage() {
  const router = useRouter();
  const [filter, setFilter] = useState<Filter>("all");
  const [markingAll, setMarkingAll] = useState(false);

  const { data, mutate } = useSWR<NotificationsResponse>(
    "/alerts/",
    fetcher,
    { refreshInterval: 60_000, revalidateOnFocus: false }
  );

  const allNotifications = data?.notifications ?? [];
  const unreadCount = data?.unread_count ?? 0;

  const filtered = allNotifications.filter((n) => {
    if (filter === "unread") return !n.is_read;
    if (filter === "read")   return n.is_read;
    return true;
  });

  const handleMarkAllRead = async () => {
    setMarkingAll(true);
    try {
      await notifications.readAll();
      await mutate();
    } finally {
      setMarkingAll(false);
    }
  };

  const handleClickRow = async (n: Notification) => {
    if (!n.is_read) {
      await notifications.read(n.id);
      await mutate();
    }
    if (n.job_id) {
      router.push(`/dashboard/jobs?job=${n.job_id}`);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between border-b-2 border-border pb-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-white uppercase tracking-tight">
            Alerts
          </h1>
          <p className="text-slate-400 font-mono text-xs mt-2 uppercase tracking-widest flex items-center gap-2">
            <Bell size={12} className="text-neon-pink" />
            {unreadCount > 0
              ? `${unreadCount} unread notification${unreadCount !== 1 ? "s" : ""}`
              : "All caught up"}
          </p>
        </div>
        {unreadCount > 0 && (
          <motion.button
            whileTap={{ scale: 0.96 }}
            onClick={handleMarkAllRead}
            disabled={markingAll}
            className="btn-ghost flex items-center gap-2 text-sm"
            id="mark-all-read-page-btn"
          >
            <CheckCheck size={16} strokeWidth={2.5} />
            {markingAll ? "Marking..." : "Mark all read"}
          </motion.button>
        )}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 border-2 border-border p-1 w-fit bg-surface-800">
        {(["all", "unread", "read"] as Filter[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-1.5 font-mono text-xs font-bold uppercase tracking-widest transition-all ${
              filter === f
                ? "bg-neon-lime text-surface-900"
                : "text-slate-400 hover:text-white"
            }`}
          >
            {f}
            {f === "unread" && unreadCount > 0 && (
              <span className="ml-1.5 text-[10px]">({unreadCount})</span>
            )}
          </button>
        ))}
      </div>

      {/* Notifications list */}
      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-slate-600 border-2 border-border bg-surface-800">
          <BellOff size={36} strokeWidth={1.5} className="mb-4 opacity-40" />
          <p className="font-mono text-sm uppercase tracking-widest">
            {filter === "unread" ? "No unread alerts" : "No alerts yet"}
          </p>
          <p className="font-mono text-xs text-slate-700 mt-2">
            High-match jobs will appear here automatically.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          <AnimatePresence mode="popLayout">
            {filtered.map((n, i) => {
              const colors = scoreColor(n.score);
              const scoreLabel = `${Math.round(n.score * 100)}%`;

              return (
                <motion.div
                  key={n.id}
                  layout
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ delay: i * 0.03, duration: 0.2 }}
                  onClick={() => handleClickRow(n)}
                  className={`brutal-panel p-4 cursor-pointer transition-all hover:translate-x-1 ${
                    !n.is_read ? "border-l-4 border-l-neon-pink" : "opacity-70"
                  }`}
                  id={`alert-row-${n.id}`}
                >
                  <div className="flex items-start gap-4">
                    {/* Score badge */}
                    <div
                      className={`shrink-0 px-2.5 py-1 border ${colors.border} ${colors.bg} ${colors.text} font-mono text-sm font-black`}
                    >
                      {scoreLabel}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-3">
                        <h3 className="font-display font-bold text-white text-sm leading-snug">
                          {n.job_title}
                        </h3>
                        <div className="flex items-center gap-2 shrink-0">
                          {!n.is_read && (
                            <span className="h-2 w-2 rounded-full bg-neon-pink" />
                          )}
                          <ExternalLink
                            size={12}
                            className="text-slate-600 hover:text-neon-lime transition-colors"
                          />
                        </div>
                      </div>
                      {n.message && (
                        <p className="text-slate-400 text-xs mt-1 leading-relaxed line-clamp-2">
                          {n.message}
                        </p>
                      )}
                      <span className="text-slate-600 font-mono text-[10px] mt-2 block">
                        {relativeTime(n.created_at)}
                      </span>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
