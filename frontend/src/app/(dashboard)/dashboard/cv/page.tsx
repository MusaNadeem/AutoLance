"use client";

import { useState, useCallback, useRef } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload, CheckCircle2, Brain,
  Zap, DollarSign, Target, RefreshCw, AlertTriangle
} from "lucide-react";
import { cv as cvApi, cvProfile } from "@/lib/api";

type ParseStatus = "idle" | "uploading" | "parsing" | "done" | "error";

const mockProfile = {
  headline: "Senior Full-Stack Engineer | Python · React · FastAPI",
  niche: "Full-Stack SaaS Development",
  experience_level: "senior",
  inferred_hourly_rate_min: 75,
  inferred_hourly_rate_max: 120,
  communication_tone: "technical",
  specializations: ["SaaS Platforms", "REST APIs", "Real-time Systems", "Cloud Architecture"],
  skills: [
    { name: "Python", level: "expert", years: 7 },
    { name: "React", level: "expert", years: 5 },
    { name: "FastAPI", level: "advanced", years: 3 },
    { name: "PostgreSQL", level: "advanced", years: 6 },
    { name: "Docker", level: "advanced", years: 4 },
    { name: "TypeScript", level: "advanced", years: 4 },
    { name: "Redis", level: "intermediate", years: 3 },
    { name: "AWS", level: "intermediate", years: 2 },
  ],
};

const levelColors: Record<string, string> = {
  expert: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
  advanced: "bg-brand-500/15 text-brand-300 border-brand-500/20",
  intermediate: "bg-violet-500/15 text-violet-400 border-violet-500/20",
  beginner: "bg-slate-500/15 text-slate-400 border-slate-500/20",
};

export default function CVPage() {
  const [status,   setStatus]   = useState<ParseStatus>("idle");
  const [fileName, setFileName] = useState<string>("");
  const [profile,  setProfile]  = useState<typeof mockProfile | null>(null);
  const [progress, setProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const onDrop = useCallback(async (files: File[]) => {
    const file = files[0];
    if (!file) return;

    setFileName(file.name);
    setUploadError(null);
    setStatus("uploading");
    setProgress(10);

    let cvId: string;
    try {
      const res = await cvApi.upload(file);
      cvId = res.data.cv_id;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setUploadError(err?.response?.data?.detail ?? "Upload failed — check file type and size");
      setStatus("error");
      return;
    }

    setStatus("parsing");
    setProgress(40);

    // Poll GET /cv/{id} until parsing_status is done or failed
    let attempts = 0;
    pollRef.current = setInterval(async () => {
      attempts++;
      setProgress(Math.min(40 + attempts * 8, 92));
      try {
        const res = await cvApi.get(cvId);
        const { parsing_status, parsed_data } = res.data;
        if (parsing_status === "done") {
          clearInterval(pollRef.current!);
          setProgress(100);
          setStatus("done");
          if (parsed_data?.skills) {
            setProfile(parsed_data as typeof mockProfile);
          } else {
            // Fallback: fetch from profile endpoint
            try {
              const pr = await cvProfile.get();
              setProfile(pr.data as unknown as typeof mockProfile);
            } catch {/* ok */}
          }
        } else if (parsing_status === "failed" || attempts > 30) {
          clearInterval(pollRef.current!);
          setUploadError("CV parsing failed. Try a different file or re-upload.");
          setStatus("error");
        }
      } catch {
        if (attempts > 30) {
          clearInterval(pollRef.current!);
          setStatus("error");
        }
      }
    }, 2000);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
    maxFiles: 1,
    disabled: status === "uploading" || status === "parsing",
  });

  return (
    <div className="p-6 max-w-5xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">CV Intelligence Engine</h1>
        <p className="text-slate-400 mt-1">Upload your resume. Claude builds your intelligence profile.</p>
      </div>

      <div
        {...getRootProps()}
        className={`relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 ${
          isDragActive
            ? "border-brand-500 bg-brand-500/5 glow-brand"
            : status === "done"
            ? "border-emerald-500/40 bg-emerald-500/5"
            : status === "error"
            ? "border-neon-pink/40 bg-neon-pink/5 hover:border-neon-pink/60"
            : "border-surface-5 hover:border-brand-500/50 hover:bg-surface-3/50"
        }`}
      >
        <input {...getInputProps()} />

        <AnimatePresence mode="wait">
          {status === "idle" && (
            <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 transition-all duration-300 ${isDragActive ? "bg-brand-500" : "bg-surface-4"}`}>
                <Upload className={`w-8 h-8 ${isDragActive ? "text-white" : "text-slate-400"}`} />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">
                {isDragActive ? "Drop your CV here" : "Upload your CV or Resume"}
              </h3>
              <p className="text-slate-400 text-sm mb-4">Drag & drop or click to browse</p>
              <div className="flex items-center justify-center gap-4 text-xs text-slate-500">
                <span className="px-2 py-1 rounded bg-surface-4 border border-surface-5">PDF</span>
                <span className="px-2 py-1 rounded bg-surface-4 border border-surface-5">DOCX</span>
                <span className="px-2 py-1 rounded bg-surface-4 border border-surface-5">TXT</span>
                <span className="text-slate-600">· Max 10MB</span>
              </div>
            </motion.div>
          )}

          {(status === "uploading" || status === "parsing") && (
            <motion.div key="parsing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="w-16 h-16 rounded-2xl bg-brand-500/15 border border-brand-500/20 flex items-center justify-center mx-auto mb-4">
                <Brain className="w-8 h-8 text-brand-400 animate-pulse" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">
                {status === "uploading" ? "Uploading..." : "Claude is analyzing your CV..."}
              </h3>
              <p className="text-slate-400 text-sm mb-6">{fileName}</p>
              <div className="max-w-xs mx-auto">
                <div className="h-1.5 bg-surface-4 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-brand rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
                <p className="text-xs text-slate-500 mt-2">{progress}% complete</p>
              </div>
            </motion.div>
          )}

          {status === "done" && (
            <motion.div key="done" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}>
              <div className="w-16 h-16 rounded-2xl bg-emerald-500/15 border border-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="w-8 h-8 text-emerald-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-1">Profile Built Successfully</h3>
              <p className="text-slate-400 text-sm">{fileName}</p>
            </motion.div>
          )}

          {status === "error" && (
            <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <div className="w-16 h-16 rounded-2xl bg-neon-pink/10 border border-neon-pink/30 flex items-center justify-center mx-auto mb-4">
                <AlertTriangle className="w-8 h-8 text-neon-pink" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-1">Upload Failed</h3>
              <p className="text-slate-400 text-sm mb-2">{uploadError}</p>
              <p className="text-slate-500 text-xs">Click to try again</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {profile && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="glass-card p-6">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h2 className="text-xl font-bold text-white">{profile.headline}</h2>
                  </div>
                  <div className="flex items-center gap-3 mt-2 flex-wrap">
                    <span className="px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-300 text-sm font-medium">
                      {profile.niche}
                    </span>
                    <span className="px-3 py-1 rounded-full bg-surface-4 border border-surface-5 text-slate-300 text-sm capitalize">
                      {profile.experience_level} Level
                    </span>
                    <span className="px-3 py-1 rounded-full bg-surface-4 border border-surface-5 text-slate-300 text-sm capitalize">
                      {profile.communication_tone} communicator
                    </span>
                  </div>
                </div>
                <button className="btn-ghost text-sm flex items-center gap-2">
                  <RefreshCw size={14} />
                  Re-analyze
                </button>
              </div>

              <div className="mt-4 flex items-center gap-2 text-slate-300">
                <DollarSign size={16} className="text-emerald-400" />
                <span className="text-sm">Inferred rate: </span>
                <span className="font-semibold text-white">
                  ${profile.inferred_hourly_rate_min}–${profile.inferred_hourly_rate_max}/hr
                </span>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div className="glass-card p-5">
                <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                  <Zap size={16} className="text-brand-400" /> Skills Detected
                </h3>
                <div className="space-y-2.5">
                  {profile.skills.map((skill) => (
                    <div key={skill.name} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-white font-medium">{skill.name}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full border ${levelColors[skill.level]}`}>
                          {skill.level}
                        </span>
                      </div>
                      <span className="text-xs text-slate-500">{skill.years}y</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass-card p-5">
                <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                  <Target size={16} className="text-violet-400" /> Specializations
                </h3>
                <div className="flex flex-wrap gap-2">
                  {profile.specializations.map((spec) => (
                    <span key={spec} className="px-3 py-1.5 rounded-xl bg-surface-4 border border-surface-5 text-slate-300 text-sm">
                      {spec}
                    </span>
                  ))}
                </div>
                <div className="mt-6 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/15">
                  <div className="flex items-start gap-2">
                    <CheckCircle2 size={14} className="text-emerald-400 mt-0.5 shrink-0" />
                    <p className="text-xs text-slate-400">
                      Your profile is active. Jobs are being scored against it every 15 minutes.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
