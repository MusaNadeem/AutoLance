"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { motion, AnimatePresence } from "framer-motion";
import { Bell, CheckCheck, ExternalLink } from "lucide-react";
import { notifications } from "@/lib/api";
import type { NotificationsResponse, Notification } from "@/types";

// ── Helpers ───────────────────────────────────────────────────────────────────

function relativeTime(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60)   return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function scoreColor(score: number): string {
  if (score >= 85) return "text-neon-lime";
  if (score >= 70) return "text-neon-cyan";
  if (score >= 50) return "text-neon-orange";
  return "text-neon-pink";
}

const fetcher = () => notifications.list().then((r) => r.data);

// ── Component ─────────────────────────────────────────────────────────────────

export function NotificationBell() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [optimisticRead, setOptimisticRead] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const { data, mutate } = useSWR<NotificationsResponse>(
    "/alerts/",
    fetcher,
    { refreshInterval: 60_000, revalidateOnFocus: false }
  );

  const unreadCount = optimisticRead ? 0 : (data?.unread_count ?? 0);
  const items = (data?.notifications ?? []).slice(0, 10);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const handleMarkAllRead = async () => {
    setOptimisticRead(true);      // instant UI update
    try {
      await notifications.readAll();
      await mutate();             // confirm with server
    } catch {
      setOptimisticRead(false);   // rollback on error
    }
  };

  const handleClickAlert = async (n: Notification) => {
    setOpen(false);
    if (!n.is_read) {
      await notifications.read(n.id);
      await mutate();
    }
    if (n.job_id) {
      router.push(`/dashboard/jobs?job=${n.job_id}`);
    }
  };

  return (
    <div ref={containerRef} className="relative" id="notification-bell">
      {/* Bell button */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative p-2 text-slate-400 hover:text-white transition-colors"
        aria-label="Notifications"
      >
        <Bell size={20} strokeWidth={2} />
        {unreadCount > 0 && (
          <motion.span
            key={unreadCount}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-neon-pink text-surface-900 text-[9px] font-black"
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </motion.span>
        )}
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.97 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-full mt-2 w-80 bg-surface-800 border-2 border-border shadow-2xl z-50"
            id="notification-dropdown"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <span className="font-mono text-xs font-bold uppercase tracking-widest text-white">
                Notifications
                {unreadCount > 0 && (
                  <span className="ml-2 text-neon-pink">{unreadCount} new</span>
                )}
              </span>
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllRead}
                  className="flex items-center gap-1 text-[10px] font-mono font-bold uppercase text-slate-400 hover:text-neon-lime transition-colors"
                  id="mark-all-read-btn"
                >
                  <CheckCheck size={12} />
                  Mark all read
                </button>
              )}
            </div>

            {/* List */}
            <div className="max-h-80 overflow-y-auto">
              {items.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 text-slate-500">
                  <Bell size={28} strokeWidth={1.5} className="mb-3 opacity-40" />
                  <p className="font-mono text-xs uppercase tracking-widest">No alerts yet</p>
                </div>
              ) : (
                items.map((n) => (
                  <motion.button
                    key={n.id}
                    whileHover={{ x: 2 }}
                    onClick={() => handleClickAlert(n)}
                    className={`w-full text-left px-4 py-3 border-b border-border transition-colors hover:bg-surface-700 ${
                      !n.is_read && !optimisticRead ? "bg-surface-700/60" : ""
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-white text-xs font-bold leading-snug line-clamp-2 flex-1">
                        {n.job_title}
                      </span>
                      <span className={`font-mono text-xs font-black shrink-0 ${scoreColor(n.score)}`}>
                        {n.score ?? 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between mt-1.5">
                      <span className="text-slate-500 font-mono text-[10px]">
                        {relativeTime(n.created_at)}
                      </span>
                      {!n.is_read && !optimisticRead && (
                        <span className="h-1.5 w-1.5 rounded-full bg-neon-pink" />
                      )}
                    </div>
                  </motion.button>
                ))
              )}
            </div>

            {/* Footer */}
            <button
              onClick={() => { setOpen(false); router.push("/dashboard/alerts"); }}
              className="w-full flex items-center justify-center gap-2 py-3 text-[10px] font-mono font-bold uppercase tracking-widest text-slate-400 hover:text-neon-lime border-t border-border transition-colors"
            >
              <ExternalLink size={10} />
              View all alerts
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default NotificationBell;
