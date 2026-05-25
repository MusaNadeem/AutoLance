"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Target, Plus, X, Loader2, ArrowRight, ChevronRight } from "lucide-react";
import { cvProfile } from "@/lib/api";
import type { CVProfile, SkillItem, ExperienceLevel } from "@/types";

const EXPERIENCE_LEVELS: { value: ExperienceLevel; label: string }[] = [
  { value: "junior",  label: "Junior (0-2 yrs)" },
  { value: "mid",     label: "Mid (2-5 yrs)"    },
  { value: "senior",  label: "Senior (5-10 yrs)" },
  { value: "expert",  label: "Expert (10+ yrs)"  },
];

// ── SkillChip ─────────────────────────────────────────────────────────────────
function SkillChip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <motion.span
      layout
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-neon-lime/10 border border-neon-lime text-neon-lime font-mono text-xs font-bold"
    >
      {label}
      <button
        onClick={onRemove}
        aria-label={`Remove ${label}`}
        className="hover:text-white transition-colors"
      >
        <X size={10} strokeWidth={3} />
      </button>
    </motion.span>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function OnboardingPage() {
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [saving,  setSaving]  = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  // Form state
  const [headline,   setHeadline]   = useState("");
  const [summary,    setSummary]    = useState("");
  const [skills,     setSkills]     = useState<SkillItem[]>([]);
  const [skillInput, setSkillInput] = useState("");
  const [expLevel,   setExpLevel]   = useState<ExperienceLevel>("mid");
  const [hourlyMin,  setHourlyMin]  = useState<string>("");
  const [hourlyMax,  setHourlyMax]  = useState<string>("");
  const [fixedMin,   setFixedMin]   = useState<string>("");
  const [fixedMax,   setFixedMax]   = useState<string>("");
  const [rateError,  setRateError]  = useState<string | null>(null);

  const skillInputRef = useRef<HTMLInputElement>(null);

  // Pre-fill from GET /cv/profile
  useEffect(() => {
    cvProfile.get()
      .then((r) => {
        const p: CVProfile = r.data;
        setHeadline(p.headline ?? "");
        setSummary(p.summary ?? "");
        setSkills(p.skills ?? []);
        setExpLevel((p.experience_level as ExperienceLevel) ?? "mid");
        setHourlyMin(p.inferred_hourly_rate_min?.toString() ?? "");
        setHourlyMax(p.inferred_hourly_rate_max?.toString() ?? "");
        setFixedMin(p.target_fixed_min?.toString() ?? "");
        setFixedMax(p.target_fixed_max?.toString() ?? "");
      })
      .catch(() => { /* No profile yet — start empty */ })
      .finally(() => setLoading(false));
  }, []);

  // ── Skill chip management ─────────────────────────────────────────────────
  const addSkill = () => {
    const name = skillInput.trim();
    if (!name) return;
    if (skills.some((s) => s.name.toLowerCase() === name.toLowerCase())) {
      setSkillInput("");
      return;
    }
    setSkills((prev) => [...prev, { name, level: "intermediate", years: 0 }]);
    setSkillInput("");
    skillInputRef.current?.focus();
  };

  const removeSkill = (name: string) =>
    setSkills((prev) => prev.filter((s) => s.name !== name));

  // ── Validation ────────────────────────────────────────────────────────────
  const validate = (): boolean => {
    const hMin = parseFloat(hourlyMin);
    const hMax = parseFloat(hourlyMax);
    const fMin = parseFloat(fixedMin);
    const fMax = parseFloat(fixedMax);

    if (hourlyMin && hourlyMax && hMin >= hMax) {
      setRateError("Hourly min must be less than max");
      return false;
    }
    if (fixedMin && fixedMax && fMin >= fMax) {
      setRateError("Fixed-price min must be less than max");
      return false;
    }
    setRateError(null);
    return true;
  };

  // ── Submit ────────────────────────────────────────────────────────────────
  const handleConfirm = async () => {
    if (!validate()) return;
    setSaving(true);
    setError(null);
    try {
      await cvProfile.update({
        headline:                 headline || undefined,
        summary:                  summary  || undefined,
        skills,
        experience_level:         expLevel,
        inferred_hourly_rate_min: hourlyMin ? parseFloat(hourlyMin) : undefined,
        inferred_hourly_rate_max: hourlyMax ? parseFloat(hourlyMax) : undefined,
        target_fixed_min:         fixedMin  ? parseFloat(fixedMin)  : undefined,
        target_fixed_max:         fixedMax  ? parseFloat(fixedMax)  : undefined,
      } as Partial<CVProfile>);
      router.push("/dashboard/jobs");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err?.response?.data?.detail ?? "Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-900">
        <Loader2 size={32} className="animate-spin text-neon-lime" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-grid-pattern flex items-start justify-center p-6 py-16">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-10">
          <div className="w-14 h-14 bg-neon-lime border-4 border-surface-900 flex items-center justify-center mx-auto mb-6 shadow-brutal-sm">
            <Target className="w-7 h-7 text-surface-900" strokeWidth={2.5} />
          </div>
          <h1 className="text-4xl font-display font-bold text-white uppercase tracking-tighter">
            Set Up Your Profile
          </h1>
          <p className="text-slate-400 font-mono text-sm mt-3 uppercase tracking-wider">
            Confirm your details so we can find the best matches for you
          </p>
        </motion.div>

        {/* Form card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="brutal-panel p-8 space-y-8"
        >
          {/* Error */}
          {error && (
            <div className="px-4 py-3 border-2 border-neon-pink bg-neon-pink/10 text-neon-pink font-mono text-sm">
              {error}
            </div>
          )}

          {/* Headline */}
          <div>
            <label className="block text-xs font-mono font-bold text-slate-400 uppercase tracking-widest mb-2">
              Professional Headline
            </label>
            <input
              id="headline-input"
              type="text"
              value={headline}
              onChange={(e) => setHeadline(e.target.value)}
              placeholder="e.g. Full-Stack Python & React Engineer"
              className="w-full bg-surface-900 border-2 border-border px-4 py-3 text-white font-mono text-sm placeholder-slate-700 focus:outline-none focus:border-neon-lime transition-colors"
            />
          </div>

          {/* Experience level */}
          <div>
            <label className="block text-xs font-mono font-bold text-slate-400 uppercase tracking-widest mb-2">
              Experience Level
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {EXPERIENCE_LEVELS.map((lvl) => (
                <button
                  key={lvl.value}
                  id={`exp-${lvl.value}`}
                  onClick={() => setExpLevel(lvl.value)}
                  className={`px-3 py-3 border-2 font-mono text-xs font-bold uppercase tracking-wider transition-all ${
                    expLevel === lvl.value
                      ? "border-neon-lime text-neon-lime bg-neon-lime/10"
                      : "border-border text-slate-400 hover:border-slate-500 hover:text-white"
                  }`}
                >
                  {lvl.label}
                </button>
              ))}
            </div>
          </div>

          {/* Skills */}
          <div>
            <label className="block text-xs font-mono font-bold text-slate-400 uppercase tracking-widest mb-2">
              Skills {skills.length > 0 && <span className="text-neon-lime">({skills.length})</span>}
            </label>
            {/* Chip list */}
            <div className="flex flex-wrap gap-2 mb-3 min-h-[2rem]">
              <AnimatePresence>
                {skills.map((s) => (
                  <SkillChip key={s.name} label={s.name} onRemove={() => removeSkill(s.name)} />
                ))}
              </AnimatePresence>
              {skills.length === 0 && (
                <span className="text-slate-600 font-mono text-xs">No skills added yet</span>
              )}
            </div>
            {/* Add input */}
            <div className="flex gap-2">
              <input
                ref={skillInputRef}
                id="skill-input"
                type="text"
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addSkill(); } }}
                placeholder="Type a skill and press Enter"
                className="flex-1 bg-surface-900 border-2 border-border px-3 py-2 text-white font-mono text-sm placeholder-slate-700 focus:outline-none focus:border-neon-lime transition-colors"
              />
              <button
                onClick={addSkill}
                className="px-3 py-2 border-2 border-border text-slate-400 hover:border-neon-lime hover:text-neon-lime transition-colors"
              >
                <Plus size={16} strokeWidth={2.5} />
              </button>
            </div>
          </div>

          {/* Rates */}
          <div>
            <label className="block text-xs font-mono font-bold text-slate-400 uppercase tracking-widest mb-3">
              Target Rates (USD)
            </label>
            {rateError && (
              <p className="text-neon-orange font-mono text-xs mb-3">{rateError}</p>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] text-slate-600 font-mono mb-1">Hourly Min $/hr</label>
                <input
                  id="hourly-min"
                  type="number" min="0" value={hourlyMin}
                  onChange={(e) => setHourlyMin(e.target.value)}
                  placeholder="50"
                  className="w-full bg-surface-900 border-2 border-border px-3 py-2 text-white font-mono text-sm placeholder-slate-700 focus:outline-none focus:border-neon-lime transition-colors"
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-600 font-mono mb-1">Hourly Max $/hr</label>
                <input
                  id="hourly-max"
                  type="number" min="0" value={hourlyMax}
                  onChange={(e) => setHourlyMax(e.target.value)}
                  placeholder="150"
                  className="w-full bg-surface-900 border-2 border-border px-3 py-2 text-white font-mono text-sm placeholder-slate-700 focus:outline-none focus:border-neon-lime transition-colors"
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-600 font-mono mb-1">Fixed Project Min $</label>
                <input
                  id="fixed-min"
                  type="number" min="0" value={fixedMin}
                  onChange={(e) => setFixedMin(e.target.value)}
                  placeholder="500"
                  className="w-full bg-surface-900 border-2 border-border px-3 py-2 text-white font-mono text-sm placeholder-slate-700 focus:outline-none focus:border-neon-lime transition-colors"
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-600 font-mono mb-1">Fixed Project Max $</label>
                <input
                  id="fixed-max"
                  type="number" min="0" value={fixedMax}
                  onChange={(e) => setFixedMax(e.target.value)}
                  placeholder="10000"
                  className="w-full bg-surface-900 border-2 border-border px-3 py-2 text-white font-mono text-sm placeholder-slate-700 focus:outline-none focus:border-neon-lime transition-colors"
                />
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <motion.button
              id="confirm-profile-btn"
              whileTap={{ scale: 0.97 }}
              onClick={handleConfirm}
              disabled={saving}
              className="flex-1 btn-primary flex items-center justify-center gap-2 py-4"
            >
              {saving ? (
                <><Loader2 size={18} className="animate-spin" /> Saving...</>
              ) : (
                <><ArrowRight size={18} strokeWidth={2.5} /> Confirm Profile</>
              )}
            </motion.button>
            <button
              id="skip-onboarding-btn"
              onClick={() => router.push("/dashboard/jobs")}
              className="px-6 py-4 border-2 border-border text-slate-400 font-mono text-sm uppercase tracking-widest hover:text-white hover:border-slate-500 transition-colors flex items-center gap-2"
            >
              Skip <ChevronRight size={14} />
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
