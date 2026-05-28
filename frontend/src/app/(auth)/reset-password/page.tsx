"use client";

import { Suspense, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Target, Eye, EyeOff, ArrowRight, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { auth } from "@/lib/api";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const router       = useRouter();
  const token        = searchParams.get("token") ?? "";

  const [password, setPassword]         = useState("");
  const [confirm, setConfirm]           = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading]           = useState(false);
  const [done, setDone]                 = useState(false);
  const [error, setError]               = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirm) { setError("Passwords don't match"); return; }
    if (password.length < 8)  { setError("Password must be at least 8 characters"); return; }
    if (!token)                { setError("Invalid reset link"); return; }

    setLoading(true);
    try {
      await auth.resetPassword(token, password);
      setDone(true);
      setTimeout(() => router.push("/login"), 2500);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err?.response?.data?.detail ?? "Reset failed. The link may have expired.");
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
          <h1 className="text-4xl font-display font-bold text-white uppercase tracking-tighter">New Password</h1>
          <p className="text-slate-400 mt-2 font-mono text-sm uppercase tracking-wider">Choose a strong password</p>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="brutal-panel p-8">
          {done ? (
            <div className="text-center space-y-4">
              <CheckCircle2 size={48} className="text-neon-lime mx-auto" strokeWidth={2} />
              <p className="text-white font-mono font-bold uppercase tracking-wide">Password updated!</p>
              <p className="text-slate-400 text-sm font-mono">Redirecting you to login...</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <div className="flex items-center gap-2 px-4 py-3 bg-neon-pink/10 border-2 border-neon-pink text-neon-pink font-mono text-sm">
                  <AlertCircle size={16} strokeWidth={2.5} />
                  {error}
                </div>
              )}
              {!token && (
                <div className="flex items-center gap-2 px-4 py-3 bg-neon-orange/10 border-2 border-neon-orange text-neon-orange font-mono text-sm">
                  <AlertCircle size={16} /> Invalid or missing reset token.{" "}
                  <Link href="/forgot-password" className="underline">Request a new link</Link>
                </div>
              )}
              <div>
                <label className="block text-sm font-mono font-bold text-slate-300 mb-2 uppercase tracking-wide">New Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"} value={password}
                    onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required
                    className="w-full bg-surface-900 border-2 border-border px-4 py-4 text-white font-mono placeholder-slate-600 focus:outline-none focus:border-neon-lime transition-colors pr-12"
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-neon-lime transition-colors">
                    {showPassword ? <EyeOff size={20} strokeWidth={2.5} /> : <Eye size={20} strokeWidth={2.5} />}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-mono font-bold text-slate-300 mb-2 uppercase tracking-wide">Confirm Password</label>
                <input
                  type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)}
                  placeholder="••••••••" required
                  className="w-full bg-surface-900 border-2 border-border px-4 py-4 text-white font-mono placeholder-slate-600 focus:outline-none focus:border-neon-lime transition-colors"
                />
              </div>
              <button type="submit" disabled={loading || !token} className="btn-primary w-full flex items-center justify-center gap-3 py-4 mt-2 disabled:opacity-50">
                {loading ? (
                  <><Loader2 size={20} className="animate-spin" strokeWidth={2.5} /> UPDATING...</>
                ) : (
                  <><span>SET NEW PASSWORD</span><ArrowRight size={20} strokeWidth={2.5} /></>
                )}
              </button>
            </form>
          )}
        </motion.div>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetPasswordForm />
    </Suspense>
  );
}
