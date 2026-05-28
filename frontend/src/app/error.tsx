"use client";

import { useEffect } from "react";
import { AlertTriangle } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-grid-pattern">
      <div className="text-center space-y-6 max-w-md">
        <div className="w-20 h-20 bg-neon-pink border-4 border-surface-900 flex items-center justify-center mx-auto shadow-brutal-sm">
          <AlertTriangle className="w-10 h-10 text-surface-900" strokeWidth={2.5} />
        </div>
        <div>
          <p className="font-mono text-neon-pink text-sm uppercase tracking-widest font-bold mb-2">Error</p>
          <h1 className="text-4xl font-display font-bold text-white uppercase tracking-tighter">Something Went Wrong</h1>
          <p className="text-slate-400 font-mono text-sm mt-3">
            {error.message || "An unexpected error occurred."}
          </p>
        </div>
        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="px-6 py-3 bg-neon-lime text-surface-900 font-mono font-bold text-sm uppercase tracking-widest hover:bg-white transition-colors"
          >
            Try Again
          </button>
          <a
            href="/dashboard"
            className="px-6 py-3 border-2 border-border text-slate-300 font-mono text-sm uppercase tracking-widest hover:border-neon-lime hover:text-neon-lime transition-colors"
          >
            Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
