"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  Target, LayoutDashboard, Briefcase, FileText,
  BarChart3, Bell, Settings, Upload, LogOut, Menu, Zap
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

const SCRAPE_INTERVAL_MINUTES = Number(process.env.NEXT_PUBLIC_SCRAPE_INTERVAL_MINUTES) || 15;

function useScrapeCountdown() {
  const intervalMs = Math.max(1, SCRAPE_INTERVAL_MINUTES * 60 * 1000);

  const computeRemainingMinutes = useCallback(() => {
    const now = Date.now();
    const nextTick = Math.ceil(now / intervalMs) * intervalMs;
    return Math.max(0, Math.ceil((nextTick - now) / 60000));
  }, [intervalMs]);

  const [remainingMinutes, setRemainingMinutes] = useState<number>(() => computeRemainingMinutes());

  // Lightweight countdown that resets every interval boundary.
  // (This is UI-only; real scraping cadence depends on backend/beat.)
  useEffect(() => {
    const id = setInterval(() => {
      setRemainingMinutes(computeRemainingMinutes());
    }, 1000);
    return () => clearInterval(id);
  }, [computeRemainingMinutes]);

  return remainingMinutes;
}

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/cv", label: "CV Intelligence", icon: Upload },
  { href: "/dashboard/jobs", label: "Job Feed", icon: Briefcase },
  { href: "/dashboard/proposals", label: "Proposals", icon: FileText },
  { href: "/dashboard/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/dashboard/alerts", label: "Alerts", icon: Bell },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const nextScrapeInMinutes = useScrapeCountdown();

  return (
    <div className="flex h-screen overflow-hidden bg-surface-900">
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-surface-800 border-r-2 border-border flex flex-col transition-transform duration-200 lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Logo */}
        <div className="h-16 flex items-center gap-3 px-6 border-b-2 border-border bg-surface-900">
          <div className="w-8 h-8 bg-neon-lime border-2 border-border shadow-brutal-sm flex items-center justify-center transition-transform hover:scale-105">
            <Target className="w-5 h-5 text-surface-900 stroke-[2.5px]" />
          </div>
          <div>
            <span className="font-display font-bold text-white uppercase tracking-wider text-sm">FreelanceRadar</span>
            <div className="flex items-center gap-1 mt-0.5">
              <div className="w-2 h-2 rounded-none bg-neon-lime animate-blink" />
              <span className="text-[10px] text-neon-lime font-bold uppercase tracking-wider">LIVE</span>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {navItems.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setSidebarOpen(false)}
                className={`nav-item ${active ? "active" : ""}`}
              >
                <item.icon className="w-5 h-5 shrink-0" strokeWidth={active ? 2.5 : 2} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* User section */}
        <div className="p-4 border-t-2 border-border bg-surface-900">
          <div className="brutal-panel p-3 flex items-center gap-3 cursor-pointer">
            <div className="w-10 h-10 bg-neon-cyan border-2 border-surface-900 flex items-center justify-center text-surface-900 font-bold font-display text-lg shrink-0">
              U
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-bold font-display uppercase tracking-wide text-white truncate">User</div>
              <div className="text-xs font-mono text-slate-400 truncate">PRO PLAN</div>
            </div>
            <button className="text-slate-500 hover:text-neon-pink transition-colors">
              <LogOut size={18} strokeWidth={2.5} />
            </button>
          </div>
        </div>
      </aside>

      {/* Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-surface-900/80 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col lg:ml-64 overflow-hidden bg-grid-pattern">
        {/* Topbar */}
        <header className="h-16 flex items-center justify-between px-6 border-b-2 border-border bg-surface-800">
          <button
            className="lg:hidden text-slate-400 hover:text-neon-lime transition-colors"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={24} strokeWidth={2.5} />
          </button>

          <div className="flex-1 lg:flex-none">
            <h1 className="text-xl font-bold font-display uppercase tracking-wide text-white">
              {pathname.split("/").pop()?.replace(/-/g, " ") || "Dashboard"}
            </h1>
          </div>

          <div className="flex items-center gap-4">
            {/* Live scraping indicator */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 border-2 border-border bg-surface-900 text-xs font-mono text-slate-300">
              <Zap size={14} className="text-neon-orange animate-pulse" strokeWidth={2.5} />
              NEXT SCRAPE: {nextScrapeInMinutes}m
            </div>
            <Link href="/dashboard/alerts">
              <button className="relative w-10 h-10 border-2 border-border bg-surface-900 flex items-center justify-center text-slate-400 hover:text-neon-lime hover:border-neon-lime transition-colors">
                <Bell size={18} strokeWidth={2.5} />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-neon-pink border-2 border-surface-900 animate-blink" />
              </button>
            </Link>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8">
          <motion.div
            key={pathname}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="h-full max-w-7xl mx-auto"
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
}
