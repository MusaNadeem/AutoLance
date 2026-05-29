"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Target, ArrowRight, Loader2, Check } from "lucide-react";

const benefits = [
  "CV analyzed by Claude AI in seconds",
  "Jobs scored 0–100 against your profile",
  "Client quality signals on every job",
  "Personalized cover letters generated instantly",
];

import { apiClient } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");
  const [form, setForm]       = useState({ name: "", email: "", password: "" });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      // 1. Register
      await apiClient.post("/auth/register", {
        email:     form.email,
        password:  form.password,
        full_name: form.name,
      });
      // 2. Redirect to verification page
      router.push(`/verify-email?email=${encodeURIComponent(form.email)}`);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e?.response?.data?.detail || "Registration failed. Try a different email.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-grid-pattern relative">
      <div className="w-full max-w-5xl grid lg:grid-cols-2 gap-16 items-center relative z-10">
        {/* Left: Benefits */}
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 bg-neon-lime border-2 border-surface-900 flex items-center justify-center shadow-brutal-sm">
              <Target className="w-6 h-6 text-surface-900" strokeWidth={2.5} />
            </div>
            <span className="font-display font-bold text-xl text-white uppercase tracking-wider">AutoLance</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-display font-bold text-white mb-6 uppercase tracking-tighter leading-none">
            Find your best Upwork jobs
            <br />
            <span className="text-neon-cyan relative inline-block mt-2">
              with AI intelligence
              <div className="absolute -bottom-1 left-0 right-0 h-1.5 bg-neon-cyan/20" />
            </span>
          </h1>
          <p className="text-slate-400 mb-10 text-lg leading-relaxed font-sans">
            Join in 30 seconds. Upload your CV and start seeing AI-ranked matches immediately.
          </p>
          <div className="space-y-4">
            {benefits.map((b) => (
              <div key={b} className="flex items-center gap-4">
                <div className="w-6 h-6 bg-neon-lime flex items-center justify-center shrink-0 border-2 border-surface-900">
                  <Check size={16} strokeWidth={3} className="text-surface-900" />
                </div>
                <span className="text-white font-mono font-bold text-sm uppercase tracking-wide">{b}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Right: Form */}
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }} className="brutal-panel p-8">
          <h2 className="text-2xl font-display font-bold text-white mb-8 uppercase tracking-wide">Create your account</h2>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="px-4 py-3 border-2 border-neon-pink bg-neon-pink/10 text-neon-pink font-mono text-sm">
                {error}
              </div>
            )}
            <div>
              <label className="block text-sm font-mono font-bold text-slate-300 mb-2 uppercase tracking-wide">Full Name</label>
              <input
                type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="ALEX JOHNSON" required
                className="w-full bg-surface-900 border-2 border-border px-4 py-4 text-white font-mono placeholder-slate-600 focus:outline-none focus:border-neon-lime transition-colors"
              />
            </div>
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
              <input
                type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="••••••••" required minLength={8}
                className="w-full bg-surface-900 border-2 border-border px-4 py-4 text-white font-mono placeholder-slate-600 focus:outline-none focus:border-neon-lime transition-colors"
              />
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-3 py-4 mt-8">
              {loading ? (
                <><Loader2 size={20} className="animate-spin" strokeWidth={2.5} /> REGISTERING...</>
              ) : (
                <><span>CREATE ACCOUNT</span><ArrowRight size={20} strokeWidth={2.5} /></>
              )}
            </button>
          </form>
          
          <div className="mt-8 pt-6 border-t-2 border-border text-center space-y-4">
            <p className="text-center text-slate-500 font-mono text-[10px] uppercase tracking-widest font-bold">
              By registering you agree to our Terms of Service.
            </p>
            <p className="text-center text-slate-400 font-mono text-sm uppercase tracking-wide">
              ALREADY HAVE AN ACCOUNT?{" "}
              <Link href="/login" className="text-neon-cyan hover:text-white font-bold transition-colors">SIGN IN →</Link>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
