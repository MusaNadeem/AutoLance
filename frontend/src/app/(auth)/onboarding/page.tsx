"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Target, Plus, X, Loader2, ArrowRight, Upload,
  Brain, AlertTriangle, CheckCircle2, ChevronRight,
} from "lucide-react";
import { cv, cvProfile } from "@/lib/api";
import type { CVProfile, SkillItem, ExperienceLevel } from "@/types";
import { useDropzone } from "react-dropzone";

const EXPERIENCE_LEVELS: { value: ExperienceLevel; label: string }[] = [
  { value: "junior",  label: "Junior (0-2 yrs)"  },
  { value: "mid",     label: "Mid (2-5 yrs)"     },
  { value: "senior",  label: "Senior (5-10 yrs)" },
  { value: "expert",  label: "Expert (10+ yrs)"  },
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
      <button onClick={onRemove} className="hover:text-white transition-colors">
        <X size={10} strokeWidth={3} />
      </button>
    </motion.span>
  );
}

type UploadStatus = "idle" | "uploading" | "parsing" | "done" | "error";

export default function OnboardingPage() {
  const router = useRouter();

  // ── Step management (1 = upload CV, 2 = confirm profile) ─────────────────
  const [step,           setStep]           = useState<1 | 2>(1);
  const [skippedCV,      setSkippedCV]      = useState(false);

  // ── CV upload state ───────────────────────────────────────────────────────
  const [uploadStatus,   setUploadStatus]   = useState<UploadStatus>("idle");
  const [uploadError,    setUploadError]    = useState<string | null>(null);
  const [cvFileName,     setCvFileName]     = useState("");
  const [cvProgress,     setCvProgress]     = useState(0);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Profile form state ────────────────────────────────────────────────────
  const [profileLoading, setProfileLoading] = useState(false);
  const [saving,         setSaving]         = useState(false);
  const [error,          setError]          = useState<string | null>(null);
  const [headline,       setHeadline]       = useState("");
  const [skills,         setSkills]         = useState<SkillItem[]>([]);
  const [skillInput,     setSkillInput]     = useState("");
  const [expLevel,       setExpLevel]       = useState<ExperienceLevel>("mid");
  const [hourlyMin,      setHourlyMin]      = useState("");
  const [hourlyMax,      setHourlyMax]      = useState("");
  const [fixedMin,       setFixedMin]       = useState("");
  const [fixedMax,       setFixedMax]       = useState("");
  const [rateError,      setRateError]      = useState<string | null>(null);
  const skillInputRef = useRef<HTMLInputElement>(null);

  // On mount: check if CV profile already exists (re-visiting onboarding)
  useEffect(() => {
    cvProfile.get()
      .then((r) => populateForm(r.data))
      .catch(() => {/* No profile yet */});
  }, []);

  function populateForm(p: CVProfile) {
    setHeadline(p.headline ?? "");
    setSkills(p.skills ?? []);
    setExpLevel((p.experience_level as ExperienceLevel) ?? "mid");
    setHourlyMin(p.inferred_hourly_rate_min?.toString() ?? "");
    setHourlyMax(p.inferred_hourly_rate_max?.toString() ?? "");
    setFixedMin(p.target_fixed_min?.toString() ?? "");
    setFixedMax(p.target_fixed_max?.toString() ?? "");
  }

  // ── CV upload + polling ───────────────────────────────────────────────────
  const handleFileDrop = useCallback(async (files: File[]) => {
    const file = files[0];
    if (!file) return;
    setCvFileName(file.name);
    setUploadError(null);
    setUploadStatus("uploading");
    setCvProgress(15);

    let cvId: string;
    try {
      const res = await cv.upload(file);
      cvId = res.data.cv_id;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setUploadError(err?.response?.data?.detail ?? "Upload failed");
      setUploadStatus("error");
      return;
    }

    setUploadStatus("parsing");
    setCvProgress(40);

    // Poll GET /cv/{id} until parsing_status is done or failed
    let attempts = 0;
    pollRef.current = setInterval(async () => {
      attempts++;
      setCvProgress(Math.min(40 + attempts * 8, 90));
      try {
        const res = await cv.get(cvId);
        const { parsing_status, parsed_data } = res.data;
        if (parsing_status === "done") {
          clearInterval(pollRef.current!);
          setCvProgress(100);
          setUploadStatus("done");
          // Populate form from parsed data
          if (parsed_data) populateForm(parsed_data as CVProfile);
          // Also load from profile endpoint to get persisted version
          try {
            const pr = await cvProfile.get();
            populateForm(pr.data);
          } catch {/* use parsed_data */}
          // Auto-advance to step 2 after a short delay
          setTimeout(() => setStep(2), 800);
        } else if (parsing_status === "failed" || attempts > 30) {
          clearInterval(pollRef.current!);
          setUploadError("CV parsing failed — you can enter your skills manually below.");
          setUploadStatus("error");
          setTimeout(() => { setSkippedCV(true); setStep(2); }, 1500);
        }
      } catch {
        if (attempts > 30) {
          clearInterval(pollRef.current!);
          setUploadError("Could not check parsing status.");
          setUploadStatus("error");
        }
      }
    }, 2000);
  }, []);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleFileDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
    maxFiles: 1,
    disabled: uploadStatus === "uploading" || uploadStatus === "parsing",
  });

  // ── Skills management ─────────────────────────────────────────────────────
  const addSkill = () => {
    const name = skillInput.trim();
    if (!name || skills.some((s) => s.name.toLowerCase() === name.toLowerCase())) {
      setSkillInput(""); return;
    }
    setSkills((prev) => [...prev, { name, level: "intermediate", years: 0 }]);
    setSkillInput("");
    skillInputRef.current?.focus();
  };

  // ── Save profile ──────────────────────────────────────────────────────────
  const handleConfirm = async () => {
    const hMin = parseFloat(hourlyMin), hMax = parseFloat(hourlyMax);
    const fMin = parseFloat(fixedMin),  fMax = parseFloat(fixedMax);
    if (hourlyMin && hourlyMax && hMin >= hMax) { setRateError("Hourly min must be less than max"); return; }
    if (fixedMin  && fixedMax  && fMin >= fMax)  { setRateError("Fixed min must be less than max"); return; }
    setRateError(null);

    setSaving(true); setError(null);
    try {
      await cvProfile.update({
        headline:                 headline  || undefined,
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

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-grid-pattern flex items-start justify-center p-6 py-12">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="w-14 h-14 bg-neon-lime border-4 border-surface-900 flex items-center justify-center mx-auto mb-5 shadow-brutal-sm">
            <Target className="w-7 h-7 text-surface-900" strokeWidth={2.5} />
          </div>
          <h1 className="text-4xl font-display font-bold text-white uppercase tracking-tighter">
            {step === 1 ? "Upload Your CV" : "Confirm Your Profile"}
          </h1>
          <p className="text-slate-400 font-mono text-sm mt-2 uppercase tracking-wider">
            {step === 1
              ? "AutoLance uses your CV to find relevant jobs"
              : "Review what we extracted — edit anything"}
          </p>
        </motion.div>

        {/* Step indicator */}
        <div className="flex items-center gap-2 justify-center mb-8 font-mono text-xs uppercase tracking-widest">
          <span className={`flex items-center gap-1.5 ${step === 1 ? "text-neon-lime" : "text-slate-500"}`}>
            <span className={`w-5 h-5 rounded-full border-2 flex items-center justify-center text-[10px] font-bold ${step === 1 ? "border-neon-lime text-neon-lime" : "border-slate-600 text-slate-600"}`}>1</span>
            Upload CV
          </span>
          <span className="text-slate-700">───</span>
          <span className={`flex items-center gap-1.5 ${step === 2 ? "text-neon-lime" : "text-slate-500"}`}>
            <span className={`w-5 h-5 rounded-full border-2 flex items-center justify-center text-[10px] font-bold ${step === 2 ? "border-neon-lime text-neon-lime" : "border-slate-600 text-slate-600"}`}>2</span>
            Confirm Profile
          </span>
        </div>

        <AnimatePresence mode="wait">
          {/* ── STEP 1: Upload CV ── */}
          {step === 1 && (
            <motion.div key="step1" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="brutal-panel p-8 space-y-6">
              {/* Dropzone */}
              <div
                {...getRootProps()}
                className={`border-2 border-dashed p-10 text-center cursor-pointer transition-all duration-200 ${
                  isDragActive                          ? "border-neon-lime bg-neon-lime/5" :
                  uploadStatus === "done"              ? "border-emerald-400 bg-emerald-500/5 cursor-default" :
                  uploadStatus === "uploading" || uploadStatus === "parsing" ? "border-brand-400/60 bg-brand-500/5 cursor-default" :
                  uploadStatus === "error"             ? "border-neon-pink bg-neon-pink/5" :
                  "border-border hover:border-neon-lime/60 hover:bg-neon-lime/5"
                }`}
              >
                <input {...getInputProps()} />
                <AnimatePresence mode="wait">
                  {uploadStatus === "idle" && (
                    <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                      <Upload size={36} className={`mx-auto mb-3 ${isDragActive ? "text-neon-lime" : "text-slate-500"}`} strokeWidth={1.5} />
                      <p className="text-white font-mono font-bold text-sm uppercase tracking-wide">
                        {isDragActive ? "Drop it here" : "Drag & drop your CV"}
                      </p>
                      <p className="text-slate-500 font-mono text-xs mt-1">or click to browse · PDF · DOCX · TXT · max 10MB</p>
                    </motion.div>
                  )}
                  {(uploadStatus === "uploading" || uploadStatus === "parsing") && (
                    <motion.div key="parsing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
                      <Brain size={36} className="mx-auto text-brand-400 animate-pulse" strokeWidth={1.5} />
                      <p className="text-white font-mono font-bold text-sm uppercase tracking-wide">
                        {uploadStatus === "uploading" ? "Uploading..." : "Claude is reading your CV..."}
                      </p>
                      <p className="text-slate-500 text-xs font-mono">{cvFileName}</p>
                      <div className="max-w-xs mx-auto h-1 bg-surface-4 rounded-full overflow-hidden">
                        <motion.div className="h-full bg-neon-lime rounded-full" animate={{ width: `${cvProgress}%` }} transition={{ duration: 0.6 }} />
                      </div>
                    </motion.div>
                  )}
                  {uploadStatus === "done" && (
                    <motion.div key="done" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-2">
                      <CheckCircle2 size={36} className="mx-auto text-emerald-400" strokeWidth={1.5} />
                      <p className="text-emerald-400 font-mono font-bold text-sm uppercase tracking-wide">CV Scanned!</p>
                      <p className="text-slate-400 text-xs font-mono">{cvFileName} — Advancing to profile review...</p>
                    </motion.div>
                  )}
                  {uploadStatus === "error" && (
                    <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-2">
                      <AlertTriangle size={36} className="mx-auto text-neon-orange" strokeWidth={1.5} />
                      <p className="text-neon-orange font-mono font-bold text-sm uppercase tracking-wide">
                        {uploadError ?? "Upload failed"}
                      </p>
                      <p className="text-slate-500 text-xs font-mono">Click to try again</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Skip warning */}
              <div className="text-center pt-2">
                <button
                  onClick={() => { setSkippedCV(true); setStep(2); }}
                  className="text-slate-600 hover:text-slate-400 font-mono text-xs uppercase tracking-widest transition-colors flex items-center gap-1.5 mx-auto"
                >
                  <AlertTriangle size={10} className="text-neon-orange" />
                  Skip CV upload — enter skills manually
                  <ChevronRight size={10} />
                </button>
                <p className="text-slate-700 font-mono text-[10px] mt-1">Scraping won&apos;t use your profile until you upload a CV</p>
              </div>
            </motion.div>
          )}

          {/* ── STEP 2: Confirm Profile ── */}
          {step === 2 && (
            <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className="brutal-panel p-8 space-y-7">
              {/* CV skipped warning */}
              {skippedCV && (
                <div className="flex items-start gap-2 px-4 py-3 border-2 border-neon-orange bg-neon-orange/10 text-neon-orange font-mono text-xs">
                  <AlertTriangle size={14} className="mt-0.5 shrink-0" />
                  <span>No CV uploaded. You can still use the app, but "Scrape Now" will use generic keywords until you upload your CV from the <a href="/dashboard/cv" className="underline hover:text-white">CV page</a>.</span>
                </div>
              )}

              {/* Error */}
              {error && (
                <div className="px-4 py-3 border-2 border-neon-pink bg-neon-pink/10 text-neon-pink font-mono text-sm">{error}</div>
              )}

              {/* Headline */}
              <div>
                <label className="block text-xs font-mono font-bold text-slate-400 uppercase tracking-widest mb-2">Professional Headline</label>
                <input
                  type="text" value={headline} onChange={(e) => setHeadline(e.target.value)}
                  placeholder="e.g. Full-Stack Python & React Engineer"
                  className="w-full bg-surface-900 border-2 border-border px-4 py-3 text-white font-mono text-sm placeholder-slate-700 focus:outline-none focus:border-neon-lime transition-colors"
                />
              </div>

              {/* Experience level */}
              <div>
                <label className="block text-xs font-mono font-bold text-slate-400 uppercase tracking-widest mb-2">Experience Level</label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {EXPERIENCE_LEVELS.map((lvl) => (
                    <button key={lvl.value} onClick={() => setExpLevel(lvl.value)}
                      className={`px-3 py-3 border-2 font-mono text-xs font-bold uppercase tracking-wider transition-all ${
                        expLevel === lvl.value ? "border-neon-lime text-neon-lime bg-neon-lime/10" : "border-border text-slate-400 hover:border-slate-500 hover:text-white"
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
                  {skills.length === 0 && <span className="text-neon-orange ml-2">— add at least 1</span>}
                </label>
                <div className="flex flex-wrap gap-2 mb-3 min-h-[2rem]">
                  <AnimatePresence>
                    {skills.map((s) => (
                      <SkillChip key={s.name} label={s.name} onRemove={() => setSkills((p) => p.filter((x) => x.name !== s.name))} />
                    ))}
                  </AnimatePresence>
                  {skills.length === 0 && <span className="text-slate-600 font-mono text-xs">No skills yet</span>}
                </div>
                <div className="flex gap-2">
                  <input
                    ref={skillInputRef} type="text" value={skillInput}
                    onChange={(e) => setSkillInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addSkill(); } }}
                    placeholder="Type a skill and press Enter"
                    className="flex-1 bg-surface-900 border-2 border-border px-3 py-2 text-white font-mono text-sm placeholder-slate-700 focus:outline-none focus:border-neon-lime transition-colors"
                  />
                  <button onClick={addSkill} className="px-3 py-2 border-2 border-border text-slate-400 hover:border-neon-lime hover:text-neon-lime transition-colors">
                    <Plus size={16} strokeWidth={2.5} />
                  </button>
                </div>
              </div>

              {/* Rates */}
              <div>
                <label className="block text-xs font-mono font-bold text-slate-400 uppercase tracking-widest mb-3">Target Rates (USD)</label>
                {rateError && <p className="text-neon-orange font-mono text-xs mb-3">{rateError}</p>}
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { id: "hMin", label: "Hourly Min $/hr", val: hourlyMin, set: setHourlyMin, ph: "50" },
                    { id: "hMax", label: "Hourly Max $/hr", val: hourlyMax, set: setHourlyMax, ph: "150" },
                    { id: "fMin", label: "Fixed Project Min $", val: fixedMin, set: setFixedMin, ph: "500" },
                    { id: "fMax", label: "Fixed Project Max $", val: fixedMax, set: setFixedMax, ph: "10000" },
                  ].map(({ id, label, val, set, ph }) => (
                    <div key={id}>
                      <label className="block text-[10px] text-slate-600 font-mono mb-1">{label}</label>
                      <input type="number" min="0" value={val} onChange={(e) => set(e.target.value)} placeholder={ph}
                        className="w-full bg-surface-900 border-2 border-border px-3 py-2 text-white font-mono text-sm placeholder-slate-700 focus:outline-none focus:border-neon-lime transition-colors" />
                    </div>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-1">
                <button onClick={() => setStep(1)} className="px-4 py-4 border-2 border-border text-slate-500 font-mono text-xs uppercase tracking-widest hover:text-white hover:border-slate-500 transition-colors">
                  ← Back
                </button>
                <motion.button
                  whileTap={{ scale: 0.97 }}
                  onClick={handleConfirm}
                  disabled={saving || skills.length === 0}
                  className="flex-1 btn-primary flex items-center justify-center gap-2 py-4 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? (
                    <><Loader2 size={18} className="animate-spin" /> Saving...</>
                  ) : (
                    <><ArrowRight size={18} strokeWidth={2.5} /> Confirm &amp; Start Matching</>
                  )}
                </motion.button>
              </div>
              {skills.length === 0 && (
                <p className="text-center text-slate-600 font-mono text-[10px] uppercase tracking-widest">Add at least 1 skill to continue</p>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
