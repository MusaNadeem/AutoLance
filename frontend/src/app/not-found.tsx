import Link from "next/link";
import { Target } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-grid-pattern">
      <div className="text-center space-y-6">
        <div className="w-20 h-20 bg-neon-lime border-4 border-surface-900 flex items-center justify-center mx-auto shadow-brutal-sm">
          <Target className="w-10 h-10 text-surface-900" strokeWidth={2.5} />
        </div>
        <div>
          <p className="font-mono text-neon-lime text-sm uppercase tracking-widest font-bold mb-2">404</p>
          <h1 className="text-5xl font-display font-bold text-white uppercase tracking-tighter">Page Not Found</h1>
          <p className="text-slate-400 font-mono text-sm mt-3 uppercase tracking-wide">
            The page you&apos;re looking for doesn&apos;t exist.
          </p>
        </div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 px-6 py-3 bg-neon-lime text-surface-900 font-mono font-bold text-sm uppercase tracking-widest hover:bg-white transition-colors"
        >
          ← Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
