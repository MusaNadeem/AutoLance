"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Target, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { auth } from "@/lib/api";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token        = searchParams.get("token") ?? "";
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("No verification token found in the URL.");
      return;
    }
    auth.verifyEmail(token)
      .then(() => setStatus("success"))
      .catch((e: unknown) => {
        const err = e as { response?: { data?: { detail?: string } } };
        setMessage(err?.response?.data?.detail ?? "Verification failed or token expired.");
        setStatus("error");
      });
  }, [token]);

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-grid-pattern">
      <div className="w-full max-w-md relative z-10">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className={`w-16 h-16 border-4 border-surface-900 flex items-center justify-center mx-auto mb-6 shadow-brutal-sm ${
            status === "success" ? "bg-neon-lime" : status === "error" ? "bg-neon-pink" : "bg-brand-500"
          }`}>
            {status === "loading" && <Loader2 className="w-8 h-8 text-white animate-spin" strokeWidth={2.5} />}
            {status === "success" && <Target className="w-8 h-8 text-surface-900" strokeWidth={2.5} />}
            {status === "error"   && <AlertCircle className="w-8 h-8 text-surface-900" strokeWidth={2.5} />}
          </div>
          <h1 className="text-4xl font-display font-bold text-white uppercase tracking-tighter">
            {status === "loading" ? "Verifying..." : status === "success" ? "Email Verified!" : "Verification Failed"}
          </h1>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="brutal-panel p-8 text-center space-y-4">
          {status === "loading" && (
            <p className="text-slate-400 font-mono text-sm">Verifying your email address...</p>
          )}

          {status === "success" && (
            <>
              <CheckCircle2 size={48} className="text-neon-lime mx-auto" strokeWidth={2} />
              <p className="text-slate-300 font-mono text-sm">Your email is confirmed. You&apos;re all set!</p>
              <Link
                href="/dashboard"
                className="inline-block mt-4 px-6 py-3 bg-neon-lime text-surface-900 font-mono font-bold text-sm uppercase tracking-widest hover:bg-white transition-colors"
              >
                Go to Dashboard →
              </Link>
            </>
          )}

          {status === "error" && (
            <>
              <p className="text-neon-pink font-mono text-sm">{message}</p>
              <Link
                href="/login"
                className="inline-block mt-4 text-slate-400 hover:text-white font-mono text-sm uppercase tracking-wide transition-colors"
              >
                ← Back to Login
              </Link>
            </>
          )}
        </motion.div>
      </div>
    </div>
  );
}

export default function VerifyPage() {
  return (
    <Suspense>
      <VerifyEmailContent />
    </Suspense>
  );
}
