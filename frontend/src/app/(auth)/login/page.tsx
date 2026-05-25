"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Target, Eye, EyeOff, ArrowRight, Loader2, AlertCircle } from "lucide-react";
import { apiClient } from "@/lib/api";

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ email: "", password: "" });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await apiClient.post("/auth/login", {
        email: form.email,
        password: form.password,
      });
      const { access_token, refresh_token } = res.data;
      localStorage.setItem("access_token", access_token);
      if (refresh_token) localStorage.setItem("refresh_token", refresh_token);

      // Phase 3: redirect to /onboarding if profile has no confirmed skills
      try {
        const profileRes = await apiClient.get("/cv/profile");
        const skills = profileRes.data?.skills ?? [];
        window.location.href = skills.length === 0 ? "/onboarding" : "/dashboard";
      } catch {
        // No profile yet (404) → onboarding
        window.location.href = "/onboarding";
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e?.response?.data?.detail || "Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-grid-pattern relative">
      <div className="w-full max-w-md relative z-10">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="w-16 h-16 bg-neon-lime border-4 border-surface-900 flex items-center justify-center mx-auto mb-6 shadow-brutal-sm">
            <Target className="w-8 h-8 text-surface-900" strokeWidth={2.5} />
          </div>
          <h1 className="text-4xl font-display font-bold text-white uppercase tracking-tighter">Welcome back</h1>
          <p className="text-slate-400 mt-2 font-mono text-sm uppercase tracking-wider">Sign in to your intelligence dashboard</p>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="brutal-panel p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="flex items-center gap-2 px-4 py-3 bg-neon-pink/10 border-2 border-neon-pink text-neon-pink font-mono text-sm">
                <AlertCircle size={16} strokeWidth={2.5} />
                {error}
              </div>
            )}
            <div>
              <label className="block text-sm font-mono font-bold text-slate-300 mb-2 uppercase tracking-wide">Email Address</label>
              <input
                type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="YOU@EXAMPLE.COM" required
                className="w-full bg-surface-900 border-2 border-border px-4 py-4 text-white font-mono placeholder-slate-600 focus:outline-none focus:border-neon-lime transition-colors"
              />
            </div>
            <div>
              <label className="block text-sm font-mono font-bold text-slate-300 mb-2 uppercase tracking-wide">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"} value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="••••••••" required
                  className="w-full bg-surface-900 border-2 border-border px-4 py-4 text-white font-mono placeholder-slate-600 focus:outline-none focus:border-neon-lime transition-colors pr-12"
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-neon-lime transition-colors">
                  {showPassword ? <EyeOff size={20} strokeWidth={2.5} /> : <Eye size={20} strokeWidth={2.5} />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-3 py-4 mt-8">
              {loading ? (
                <><Loader2 size={20} className="animate-spin" strokeWidth={2.5} /> AUTHENTICATING...</>
              ) : (
                <><span>SIGN IN</span><ArrowRight size={20} strokeWidth={2.5} /></>
              )}
            </button>
          </form>
          <div className="mt-8 pt-6 border-t-2 border-border text-center">
            <p className="text-slate-400 font-mono text-sm uppercase tracking-wide">
              NO ACCOUNT?{" "}
              <Link href="/register" className="text-neon-lime hover:text-white font-bold transition-colors">CREATE ONE FREE →</Link>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
