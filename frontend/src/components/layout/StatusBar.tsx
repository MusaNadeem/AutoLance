"use client";

import { useRef, useEffect, useState } from "react";
import useSWR, { mutate } from "swr";
import { motion } from "framer-motion";
import { Zap, AlertTriangle, CheckCircle, Clock, RefreshCw } from "lucide-react";
import { scrape, apiClient } from "@/lib/api";
import type { ScrapeStatus } from "@/types";

// ── Helpers ───────────────────────────────────────────────────────────────────

function relativeTime(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

function minutesUntil(iso: string): number {
  return Math.max(0, Math.ceil((new Date(iso).getTime() - Date.now()) / 60_000));
}

const fetcher = () => scrape.status().then((r) => r.data);

// ── Component ─────────────────────────────────────────────────────────────────

export function StatusBar() {
  const prevRunning = useRef<boolean | null>(null);
  const triggeringRef = useRef(false);
  const [, setTick]         = useState(0);
  const [scrapeError, setScrapeError] = useState<string | null>(null);

  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), 1_000);
    return () => clearInterval(interval);
  }, []);

  const { data, mutate: mutateStatus } = useSWR<ScrapeStatus>(
    "/scrape/status",
    fetcher,
    {
      refreshInterval: 60_000, // fallback poll every 60s (SSE handles faster updates)
      revalidateOnFocus: false,
      onSuccess(data) {
        if (prevRunning.current === true && !data.is_running) {
          mutate("/jobs");
        }
        prevRunning.current = data.is_running;
      },
    }
  );

  // SSE connection for real-time status — supplements the SWR poll
  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("access_token");
    if (!token) return;

    const baseUrl = apiClient.defaults.baseURL ?? "http://localhost:8000/api/v1";
    const es = new EventSource(`${baseUrl}/scrape/stream?token=${encodeURIComponent(token)}`);

    es.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data) as { is_running: boolean; new_jobs: number };
        const wasRunning = prevRunning.current;
        prevRunning.current = payload.is_running;
        // When scrape finishes, immediately refresh status + jobs
        if (wasRunning && !payload.is_running) {
          mutateStatus();
          mutate("/jobs");
        }
      } catch {/* ignore parse errors */}
    };

    es.onerror = () => es.close(); // close on error; SWR poll takes over

    return () => es.close();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleTrigger = async () => {
    if (triggeringRef.current || data?.is_running) return;
    triggeringRef.current = true;
    setScrapeError(null);
    try {
      await scrape.trigger();
      await mutateStatus();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string }; status?: number } };
      const detail = err?.response?.data?.detail ?? "Trigger failed";
      setScrapeError(detail);
      setTimeout(() => setScrapeError(null), 6000);
    } finally {
      triggeringRef.current = false;
    }
  };

  if (!data) return <StatusBarSkeleton />;

  const { is_running, last_run, next_run_at } = data;

  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-surface-900 border-b-2 border-border text-xs font-mono" style={{ borderLeft: '3px solid #a3e635' }}>
      {/* Status indicator */}
      <StatusDot status={is_running ? "running" : last_run?.status ?? "idle"} />

      {/* Status text */}
      <span className="text-slate-400 uppercase tracking-widest">
        {is_running ? (
          <span className="text-neon-orange">Scraping now...</span>
        ) : last_run?.status === "failed" ? (
          <span className="text-neon-pink">
            Last scrape failed · {(last_run.error_message || "Unknown error").slice(0, 60)}
          </span>
        ) : last_run ? (
          <span className="text-slate-400">
            Last scraped{" "}
            <span className="text-white">{relativeTime(last_run.completed_at ?? last_run.started_at)}</span>
            {" · "}
            <span className="text-neon-lime">{last_run.jobs_new ?? 0} new jobs</span>
          </span>
        ) : (
          <span className="text-slate-500">No scrapes yet</span>
        )}
      </span>

      {/* CV-required error toast */}
      {scrapeError && (
        <span className="flex items-center gap-1 text-neon-orange text-[10px] font-mono">
          <AlertTriangle size={10} />
          {scrapeError.length > 70 ? scrapeError.slice(0, 70) + "…" : scrapeError}
          {scrapeError.toLowerCase().includes("cv") && (
            <a href="/dashboard/cv" className="underline hover:text-white ml-1">Upload CV →</a>
          )}
        </span>
      )}

      {/* Next run countdown */}
      {next_run_at && !is_running && !scrapeError && (
        <span className="text-slate-600 flex items-center gap-1">
          <Clock size={10} />
          Next in {minutesUntil(next_run_at)}m
        </span>
      )}

      <div className="flex-1" />

      {/* Scrape Now button */}
      <motion.button
        id="scrape-now-btn"
        onClick={handleTrigger}
        disabled={is_running}
        whileTap={{ scale: 0.95 }}
        className={`flex items-center gap-1.5 px-3 py-1 border font-mono text-[10px] font-bold uppercase tracking-widest transition-all ${is_running
          ? "border-neon-orange text-neon-orange cursor-not-allowed opacity-60"
          : "border-neon-lime text-neon-lime hover:bg-neon-lime hover:text-surface-900 cursor-pointer"
          }`}
      >
        {is_running ? (
          <>
            <RefreshCw size={10} className="animate-spin" />
            Running...
          </>
        ) : (
          <>
            <Zap size={10} />
            Scrape Now
          </>
        )}
      </motion.button>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function StatusDot({ status }: { status: string }) {
  if (status === "running") {
    return (
      <span className="relative flex h-2.5 w-2.5">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-neon-orange opacity-75" />
        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-neon-orange" />
      </span>
    );
  }
  if (status === "failed") {
    return (
      <AlertTriangle size={12} className="text-neon-pink" strokeWidth={2.5} />
    );
  }
  if (status === "completed") {
    return (
      <CheckCircle size={12} className="text-neon-lime" strokeWidth={2.5} />
    );
  }
  return (
    <span className="inline-flex rounded-full h-2.5 w-2.5 bg-slate-600" />
  );
}

function StatusBarSkeleton() {
  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-surface-900 border-b-2 border-border" style={{ borderLeft: '3px solid #a3e635' }}>
      <div className="h-2.5 w-2.5 rounded-full bg-surface-600 animate-pulse" />
      <div className="h-3 w-56 bg-surface-600 rounded animate-pulse" />
      <span className="text-[10px] text-slate-600 font-mono uppercase tracking-widest">Loading status...</span>
    </div>
  );
}

export default StatusBar;
