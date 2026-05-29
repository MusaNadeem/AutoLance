"use client";

import { useState, Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { auth } from "@/lib/api";
import { Loader2 } from "lucide-react";
import Link from "next/link";

function VerifyEmailForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "";

  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [countdown, setCountdown] = useState(60);
  const [resending, setResending] = useState(false);

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleResend = async () => {
    if (countdown > 0) return;
    setResending(true);
    setError(null);
    try {
      await auth.resendOtp(email);
      setCountdown(60);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e?.response?.data?.detail || "Failed to resend code.");
    } finally {
      setResending(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError("Email address is missing.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await auth.verifyOtp(email, otp);
      setSuccess(true);
      setTimeout(() => {
        router.push("/login");
      }, 2000);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e?.response?.data?.detail || "Invalid or expired verification code.");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="w-full max-w-md mx-auto p-8 rounded-2xl bg-[#1A1A2E]/80 backdrop-blur-xl border border-[#2D2D4E] shadow-[0_8px_32px_rgba(0,0,0,0.4)] text-center">
        <h2 className="text-2xl font-bold text-white mb-2 tracking-tight">Email Verified</h2>
        <p className="text-[#A78BFA]">Your email has been successfully verified. Redirecting to login...</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md mx-auto p-8 rounded-2xl bg-[#1A1A2E]/80 backdrop-blur-xl border border-[#2D2D4E] shadow-[0_8px_32px_rgba(0,0,0,0.4)] relative overflow-hidden group">
      <div className="absolute inset-0 bg-gradient-to-br from-[#6366F1]/10 to-[#8B5CF6]/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

      <div className="text-center mb-8 relative z-10">
        <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-[#E2E8F0] mb-2 tracking-tight">
          Verify Your Email
        </h2>
        <p className="text-[#94A3B8] text-sm font-medium">
          Enter the 6-digit code sent to <span className="text-[#A78BFA]">{email}</span>
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5 relative z-10">
        {error && (
          <div className="p-3 text-sm font-medium text-red-400 bg-red-400/10 border border-red-400/20 rounded-xl">
            {error}
          </div>
        )}

        <div className="space-y-1">
          <label className="text-sm font-semibold text-[#E2E8F0] block ml-1">
            Verification Code
          </label>
          <div className="relative">
            <input
              type="text"
              required
              maxLength={6}
              className="w-full px-4 py-3 rounded-xl bg-[#0F0F1A] border border-[#2D2D4E] text-white placeholder-[#475569] focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1] transition-all duration-300 font-mono text-center text-2xl tracking-widest"
              placeholder="000000"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || otp.length < 6}
          className="w-full bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] hover:from-[#4F46E5] hover:to-[#7C3AED] text-white font-bold py-3.5 px-4 rounded-xl transition-all duration-300 transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(99,102,241,0.3)] hover:shadow-[0_0_25px_rgba(99,102,241,0.5)]"
        >
          {loading ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              <span>Verifying...</span>
            </>
          ) : (
            <span>Verify Account</span>
          )}
        </button>

        <div className="pt-2 text-center text-sm font-medium relative z-10">
          <span className="text-[#94A3B8]">Didn&apos;t receive the code? </span>
          <button
            type="button"
            onClick={handleResend}
            disabled={countdown > 0 || resending}
            className="text-[#A78BFA] hover:text-[#C4B5FD] transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-bold"
          >
            {resending ? "Resending..." : countdown > 0 ? `Resend in ${countdown}s` : "Resend code"}
          </button>
        </div>
      </form>

      <div className="mt-6 text-center text-sm font-medium relative z-10">
        <Link
          href="/login"
          className="text-[#94A3B8] hover:text-white transition-colors duration-200"
        >
          Back to Login
        </Link>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="flex justify-center p-8"><Loader2 className="animate-spin text-[#6366F1]" /></div>}>
      <VerifyEmailForm />
    </Suspense>
  );
}
