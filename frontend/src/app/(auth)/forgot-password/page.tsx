"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Target, ArrowRight, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { auth } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail]     = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent]       = useState(false);
  const [error, setError]     = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await auth.forgotPassword(email);
      setSent(true);
    } catch {
      setError("Something went wrong. Please try again.");
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
          <h1 className="text-4xl font-display font-bold text-white uppercase tracking-tighter">Forgot Password</h1>
          <p className="text-slate-400 mt-2 font-mono text-sm uppercase tracking-wider">We&apos;ll send a reset link to your email</p>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="brutal-panel p-8">
          {sent ? (
            <div className="text-center space-y-4">
              <CheckCircle2 size={48} className="text-neon-lime mx-auto" strokeWidth={2} />
              <p className="text-white font-mono font-bold uppercase tracking-wide">Check your inbox</p>
              <p className="text-slate-400 text-sm font-mono">
                If <span className="text-white">{email}</span> has an account, we&apos;ve sent a reset link. It expires in 1 hour.
              </p>
              <Link href="/login" className="block mt-6 text-neon-lime hover:text-white font-mono text-sm uppercase tracking-widest font-bold transition-colors">
                ← Back to login
              </Link>
            </div>
          ) : (
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
                  type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                  placeholder="YOU@EXAMPLE.COM" required
                  className="w-full bg-surface-900 border-2 border-border px-4 py-4 text-white font-mono placeholder-slate-600 focus:outline-none focus:border-neon-lime transition-colors"
                />
              </div>
              <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-3 py-4 mt-4">
                {loading ? (
                  <><Loader2 size={20} className="animate-spin" strokeWidth={2.5} /> SENDING...</>
                ) : (
                  <><span>SEND RESET LINK</span><ArrowRight size={20} strokeWidth={2.5} /></>
                )}
              </button>
            </form>
          )}

          {!sent && (
            <div className="mt-8 pt-6 border-t-2 border-border text-center">
              <Link href="/login" className="text-slate-400 hover:text-white font-mono text-sm uppercase tracking-wide transition-colors">
                ← Back to login
              </Link>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
