"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Target, Eye, EyeOff, ArrowRight, Loader2 } from "lucide-react";

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ email: "", password: "" });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // In a real app, you would call your API here
    setTimeout(() => { setLoading(false); window.location.href = "/dashboard"; }, 1500);
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
