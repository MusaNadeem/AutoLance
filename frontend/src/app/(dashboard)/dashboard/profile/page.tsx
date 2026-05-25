"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Save, Plus, X, Loader2, Check, Upload, AlertTriangle,
} from "lucide-react";
import { cvProfile } from "@/lib/api";
import type { CVProfile, SkillItem, ExperienceLevel } from "@/types";

const EXPERIENCE_LEVELS: { value: ExperienceLevel; label: string }[] = [
  { value: "junior",  label: "Junior (0-2 yrs)"  },
  { value: "mid",     label: "Mid (2-5 yrs)"      },
  { value: "senior",  label: "Senior (5-10 yrs)"  },
  { value: "expert",  label: "Expert (10+ yrs)"   },
];

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
      <button onClick={onRemove} aria-label={`Remove ${label}`} className="hover:text-white transition-colors">
        <X size={10} strokeWidth={3} />
      </button>
    </motion.span>
  );
}

export default function ProfilePage() {
  const [loading,    setLoading]    = useState(true);
  const [saving,     setSaving]     = useState(false);
  const [saved,      setSaved]      = useState(false);
  const [error,      setError]      = useState<string | null>(null);
  const [rateError,  setRateError]  = useState<string | null>(null);

  // Form state
  const [headline,   setHeadline]   = useState("");
  const [summary,    setSummary]    = useState("");
  const [skills,     setSkills]     = useState<SkillItem[]>([]);
  const [skillInput, setSkillInput] = useState("");
  const [expLevel,   setExpLevel]   = useState<ExperienceLevel>("mid");
  const [hourlyMin,  setHourlyMin]  = useState("");
  const [hourlyMax,  setHourlyMax]  = useState("");
  const [fixedMin,   setFixedMin]   = useState("");
  const [fixedMax,   setFixedMax]   = useState("");

  const skillInputRef = useRef<HTMLInputElement>(null);

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
      .catch(() => setError("Could not load your profile. Please refresh."))
      .finally(() => setLoading(false));
  }, []);

  const addSkill = () => {
    const name = skillInput.trim();
    if (!name) return;
    if (skills.some((s) => s.name.toLowerCase() === name.toLowerCase())) { setSkillInput(""); return; }
    setSkills((prev) => [...prev, { name, level: "intermediate", years: 0 }]);
    setSkillInput("");
    skillInputRef.current?.focus();
  };

  const validate = (): boolean => {
    const hMin = parseFloat(hourlyMin), hMax = parseFloat(hourlyMax);
    const fMin = parseFloat(fixedMin),  fMax = parseFloat(fixedMax);
    if (hourlyMin && hourlyMax && hMin >= hMax) { setRateError("Hourly min must be less than max"); return false; }
    if (fixedMin && fixedMax   && fMin >= fMax) { setRateError("Fixed min must be less than max"); return false; }
    setRateError(null);
    return true;
  };

  const handleSave = async () => {
    if (!validate()) return;
    setSaving(true); setError(null);
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
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err?.response?.data?.detail ?? "Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto space-y-6 animate-pulse">
        {/* Header skeleton */}
        <div className="flex items-center justify-between border-b-2 border-border pb-4">
          <div className="space-y-2">
            <div className="h-8 w-32 bg-surface-700" />
            <div className="h-3 w-56 bg-surface-700" />
          </div>
          <div className="h-9 w-28 bg-surface-700" />
        </div>
        {/* Form skeleton */}
        <div className="brutal-panel p-8 space-y-8">
          <div className="space-y-2"><div className="h-3 w-40 bg-surface-700" /><div className="h-10 bg-surface-700" /></div>
          <div className="space-y-2"><div className="h-3 w-24 bg-surface-700" /><div className="h-24 bg-surface-700" /></div>
          <div className="space-y-3"><div className="h-3 w-36 bg-surface-700" /><div className="grid grid-cols-4 gap-2">{[0,1,2,3].map(i=><div key={i} className="h-12 bg-surface-700" />)}</div></div>
          <div className="space-y-2"><div className="h-3 w-20 bg-surface-700" /><div className="h-10 bg-surface-700" /></div>
          <div className="h-14 bg-surface-700" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b-2 border-border pb-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-white uppercase tracking-tight">Profile</h1>
          <p className="text-slate-400 font-mono text-xs mt-2 uppercase tracking-widest">
            Your confirmed freelancer profile · used for AI matching
          </p>
        </div>
        <a
          href="/dashboard/cv"
          className="flex items-center gap-2 px-4 py-2 border-2 border-border text-slate-400 font-mono text-xs uppercase tracking-widest hover:border-neon-lime hover:text-neon-lime transition-colors"
        >
          <Upload size={14} strokeWidth={2.5} />
          Re-upload CV
        </a>
      </div>

      {/* Errors / success */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-3 border-2 border-neon-pink bg-neon-pink/10 text-neon-pink font-mono text-sm">
          <AlertTriangle size={14} /> {error}
        </div>
      )}

      <AnimatePresence>
        {saved && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="flex items-center gap-2 px-4 py-3 border-2 border-neon-lime bg-neon-lime/10 text-neon-lime font-mono text-sm"
          >
            <Check size={14} strokeWidth={2.5} /> Profile saved successfully
          </motion.div>
        )}
      </AnimatePresence>

      {/* Form */}
      <div className="brutal-panel p-8 space-y-8">
        {/* Headline */}
        <div>
          <label className="block text-xs font-mono font-bold text-slate-400 uppercase tracking-widest mb-2">
            Professional Headline
          </label>
          <input
            id="profile-headline"
            type="text"
            value={headline}
            onChange={(e) => setHeadline(e.target.value)}
            placeholder="e.g. Full-Stack Python & React Engineer"
            className="w-full bg-surface-900 border-2 border-border px-4 py-3 text-white font-mono text-sm placeholder-slate-700 focus:outline-none focus:border-neon-lime transition-colors"
          />
        </div>

        {/* Summary */}
        <div>
          <label className="block text-xs font-mono font-bold text-slate-400 uppercase tracking-widest mb-2">
            Summary
          </label>
          <textarea
            id="profile-summary"
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            rows={4}
            placeholder="Short professional summary used in cover letter generation..."
            className="w-full bg-surface-900 border-2 border-border px-4 py-3 text-white font-mono text-sm placeholder-slate-700 focus:outline-none focus:border-neon-lime transition-colors resize-none"
          />
        </div>

        {/* Experience level */}
        <div>
          <label className="block text-xs font-mono font-bold text-slate-400 uppercase tracking-widest mb-3">
            Experience Level
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {EXPERIENCE_LEVELS.map((lvl) => (
              <button
                key={lvl.value}
                id={`profile-exp-${lvl.value}`}
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
          <div className="flex flex-wrap gap-2 mb-3 min-h-[2rem]">
            <AnimatePresence>
              {skills.map((s) => (
                <SkillChip
                  key={s.name}
                  label={s.name}
                  onRemove={() => setSkills((p) => p.filter((x) => x.name !== s.name))}
                />
              ))}
            </AnimatePresence>
            {skills.length === 0 && (
              <span className="text-slate-600 font-mono text-xs">No skills yet</span>
            )}
          </div>
          <div className="flex gap-2">
            <input
              ref={skillInputRef}
              id="profile-skill-input"
              type="text"
              value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addSkill(); } }}
              placeholder="Type skill and press Enter"
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
          {rateError && <p className="text-neon-orange font-mono text-xs mb-3">{rateError}</p>}
          <div className="grid grid-cols-2 gap-4">
            {[
              { id: "profile-hourly-min", label: "Hourly Min $/hr",    val: hourlyMin, set: setHourlyMin, ph: "50"     },
              { id: "profile-hourly-max", label: "Hourly Max $/hr",    val: hourlyMax, set: setHourlyMax, ph: "150"    },
              { id: "profile-fixed-min",  label: "Fixed Project Min $", val: fixedMin,  set: setFixedMin,  ph: "500"   },
              { id: "profile-fixed-max",  label: "Fixed Project Max $", val: fixedMax,  set: setFixedMax,  ph: "10000" },
            ].map((field) => (
              <div key={field.id}>
                <label className="block text-[10px] text-slate-600 font-mono mb-1">{field.label}</label>
                <input
                  id={field.id}
                  type="number" min="0"
                  value={field.val}
                  onChange={(e) => field.set(e.target.value)}
                  placeholder={field.ph}
                  className="w-full bg-surface-900 border-2 border-border px-3 py-2 text-white font-mono text-sm placeholder-slate-700 focus:outline-none focus:border-neon-lime transition-colors"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Save */}
        <motion.button
          id="save-profile-btn"
          whileTap={{ scale: 0.97 }}
          onClick={handleSave}
          disabled={saving}
          className="w-full btn-primary flex items-center justify-center gap-2 py-4"
        >
          {saving ? (
            <><Loader2 size={18} className="animate-spin" /> Saving...</>
          ) : (
            <><Save size={18} strokeWidth={2.5} /> Save Changes</>
          )}
        </motion.button>
      </div>
    </div>
  );
}
