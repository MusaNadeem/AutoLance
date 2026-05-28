"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Copy, Check, ExternalLink, RefreshCw, Loader2,
  AlertTriangle, Send, History, ChevronDown,
} from "lucide-react";
import useSWR from "swr";
import { coverLetters, proposals } from "@/lib/api";
import type { Job, ProposalTone } from "@/types";

// ── Types ─────────────────────────────────────────────────────────────────────

interface ProposalPanelProps {
  job: Job;
  initialContent?: string;
}

const TONES: { value: ProposalTone; label: string; desc: string }[] = [
  { value: "professional", label: "Professional", desc: "Formal · Results-focused" },
  { value: "friendly",     label: "Friendly",     desc: "Warm · Conversational" },
  { value: "bold",         label: "Bold",          desc: "Direct · Value-first" },
];

const CHAR_LIMIT     = 5000;
const CHAR_WARN      = 4500;
const WORD_MIN       = 50;
const WORD_MAX       = 250;

// ── Helpers ───────────────────────────────────────────────────────────────────

function wordCount(text: string): number {
  return text.trim() ? text.trim().split(/\s+/).length : 0;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function ProposalPanel({
  job,
  initialContent = "",
}: ProposalPanelProps) {
  const [text, setText]           = useState(initialContent);
  const [tone, setTone]           = useState<ProposalTone>("professional");
  const [generating, setGenerating] = useState(false);
  const [error, setError]         = useState<string | null>(null);
  const [copied, setCopied]           = useState(false);
  const [isDirty, setIsDirty]         = useState(false);
  const [confirmRegen, setConfirmRegen] = useState(false);
  const [saving, setSaving]           = useState(false);
  const [saved, setSaved]             = useState(false);
  const [letterId, setLetterId]       = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);

  const { data: history } = useSWR(
    showHistory ? `/cover-letters?job_id=${job.id}` : null,
    () => coverLetters.listForJob(job.id).then((r) => r.data as Array<{ id: string; style: string; variant_index: number; created_at: string }>),
    { revalidateOnFocus: false }
  );

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const chars  = text.length;
  const words  = wordCount(text);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [text]);

  const generate = useCallback(async (selectedTone: ProposalTone) => {
    setGenerating(true);
    setError(null);
    try {
      const res = await coverLetters.generate({
        job_id: job.id,
        tone: selectedTone,
      });
      setText(res.data.content ?? "");
      setLetterId(res.data.id ?? null);
      setIsDirty(false);
      setSaved(false);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err?.response?.data?.detail ?? "Failed to generate proposal");
    } finally {
      setGenerating(false);
    }
  }, [job.id]);

  // Auto-generate on mount if no initial content
  useEffect(() => {
    if (!initialContent) generate("professional");
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleToneSelect = (newTone: ProposalTone) => {
    setTone(newTone);
    // Tone change does NOT auto-regenerate — user picks a tone then clicks Regenerate.
    // This avoids the textarea reloading every time a tone button is clicked.
  };

  const handleRegenerate = () => {
    if (isDirty) {
      setConfirmRegen(true);
    } else {
      generate(tone);
    }
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const charColor =
    chars > CHAR_WARN ? "text-neon-pink" : chars > CHAR_LIMIT * 0.8 ? "text-neon-orange" : "text-slate-500";

  return (
    <div className="space-y-4">
      {/* Tone selector */}
      <div>
        <p className="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-widest mb-2">
          Proposal Tone
        </p>
        <div className="flex gap-2 flex-wrap">
          {TONES.map((t) => (
            <button
              key={t.value}
              id={`tone-${t.value}`}
              onClick={() => handleToneSelect(t.value)}
              disabled={generating}
              className={`px-3 py-2 border-2 font-mono text-xs font-bold uppercase tracking-wider transition-all ${
                tone === t.value
                  ? "border-neon-lime text-neon-lime bg-neon-lime/10"
                  : "border-border text-slate-400 hover:border-slate-500 hover:text-white"
              } disabled:opacity-40 disabled:cursor-not-allowed`}
            >
              {t.label}
              <span className="block text-[9px] font-normal normal-case tracking-normal opacity-60 mt-0.5">
                {t.desc}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 px-3 py-2 border-2 border-neon-pink bg-neon-pink/10 text-neon-pink font-mono text-xs">
          <AlertTriangle size={14} strokeWidth={2.5} />
          {error}
        </div>
      )}

      {/* Textarea */}
      <div className="relative">
        {generating && (
          <div className="absolute inset-0 bg-surface-900/80 flex items-center justify-center z-10 border-2 border-neon-lime/30">
            <Loader2 size={24} className="animate-spin text-neon-lime" />
            <span className="ml-2 font-mono text-xs text-neon-lime uppercase tracking-widest">Generating...</span>
          </div>
        )}
        <textarea
          ref={textareaRef}
          id="proposal-textarea"
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            setIsDirty(true);
          }}
          disabled={generating}
          placeholder="Your proposal will appear here..."
          className="w-full min-h-48 bg-surface-900 border-2 border-border px-4 py-3 text-white font-mono text-sm leading-relaxed placeholder-slate-700 focus:outline-none focus:border-neon-lime transition-colors resize-none disabled:opacity-50"
          maxLength={CHAR_LIMIT}
        />
      </div>

      {/* Char counter + word count */}
      <div className="flex items-center justify-between text-[10px] font-mono">
        <div className="flex gap-4">
          <span className={charColor}>
            {chars.toLocaleString()} / {CHAR_LIMIT.toLocaleString()} chars
          </span>
          <span className={
            words < WORD_MIN ? "text-neon-orange" :
            words > WORD_MAX ? "text-neon-orange" : "text-slate-600"
          }>
            {words} words
            {words < WORD_MIN && words > 0 && " · Too short (min 50)"}
            {words > WORD_MAX && " · Too long (max 250)"}
          </span>
        </div>
          <span className={`text-[10px] font-mono uppercase tracking-widest text-slate-600`}>
            Regenerate with {tone}
          </span>
          <button
            onClick={handleRegenerate}
            disabled={generating}
            className="flex items-center gap-1 text-slate-500 hover:text-neon-lime transition-colors uppercase tracking-widest disabled:opacity-40"
          >
            <RefreshCw size={10} className={generating ? "animate-spin" : ""} />
            Regenerate
          </button>
      </div>

      {/* Action buttons */}
      <div className="flex gap-2 pt-1 flex-wrap">
        <motion.button
          id="copy-proposal-btn"
          whileTap={{ scale: 0.97 }}
          onClick={handleCopy}
          disabled={!text || generating}
          className="flex-1 flex items-center justify-center gap-2 py-3 border-2 border-border font-mono text-xs font-bold uppercase tracking-widest text-slate-300 hover:border-neon-lime hover:text-neon-lime transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <AnimatePresence mode="wait">
            {copied ? (
              <motion.span key="copied" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex items-center gap-2 text-neon-lime">
                <Check size={14} strokeWidth={2.5} /> Copied!
              </motion.span>
            ) : (
              <motion.span key="copy" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex items-center gap-2">
                <Copy size={14} strokeWidth={2.5} /> Copy
              </motion.span>
            )}
          </AnimatePresence>
        </motion.button>

        {/* Apply + Track */}
        <motion.button
          whileTap={{ scale: 0.97 }}
          disabled={!text || generating || saving || saved}
          onClick={async () => {
            setSaving(true);
            try {
              await proposals.create({
                job_id: job.id,
                cover_letter_id: letterId ?? undefined,
                bid_amount: job.bid?.recommended ?? undefined,
              });
              setSaved(true);
            } finally {
              setSaving(false);
            }
          }}
          className="flex-1 flex items-center justify-center gap-2 py-3 border-2 font-mono text-xs font-bold uppercase tracking-widest transition-all disabled:opacity-40 disabled:cursor-not-allowed border-neon-cyan text-neon-cyan hover:bg-neon-cyan/10 data-[saved=true]:border-emerald-400 data-[saved=true]:text-emerald-400"
          data-saved={saved}
        >
          {saving ? (
            <><Loader2 size={14} className="animate-spin" /> Saving...</>
          ) : saved ? (
            <><Check size={14} /> Tracked!</>
          ) : (
            <><Send size={14} strokeWidth={2.5} /> Apply + Track</>
          )}
        </motion.button>

        {job.url && (
          <a
            id="open-upwork-btn"
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 px-4 py-3 border-2 border-border font-mono text-xs font-bold uppercase tracking-widest text-slate-400 hover:border-neon-cyan hover:text-neon-cyan transition-all"
          >
            <ExternalLink size={14} strokeWidth={2.5} />
            Upwork
          </a>
        )}
      </div>

      {/* Cover letter history */}
      <div className="border-t border-border pt-3">
        <button
          onClick={() => setShowHistory(!showHistory)}
          className="flex items-center gap-2 text-[10px] font-mono font-bold text-slate-500 hover:text-white uppercase tracking-widest transition-colors w-full"
        >
          <History size={11} />
          Past Variants
          <ChevronDown size={11} className={`ml-auto transition-transform ${showHistory ? "rotate-180" : ""}`} />
        </button>
        <AnimatePresence>
          {showHistory && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="pt-2 flex flex-wrap gap-2">
                {!history && (
                  <span className="text-xs text-slate-600 font-mono">Loading...</span>
                )}
                {history?.length === 0 && (
                  <span className="text-xs text-slate-600 font-mono">No past variants yet.</span>
                )}
                {history?.map((l) => (
                  <button
                    key={l.id}
                    onClick={() => {
                      // Reload this variant — fetch content from backend via re-generate with same id
                      coverLetters.list().then((r) => {
                        const found = (r.data as Array<{id: string; content?: string}>).find((x) => x.id === l.id);
                        if (found?.content) { setText(found.content); setIsDirty(false); setLetterId(l.id); }
                      });
                    }}
                    className="px-2 py-1 bg-surface-4 border border-surface-5 text-slate-300 hover:border-neon-lime hover:text-neon-lime text-[10px] font-mono uppercase tracking-wider transition-colors"
                  >
                    v{l.variant_index} · {l.style}
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Regenerate confirm dialog */}
      <AnimatePresence>
        {confirmRegen && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="border-2 border-neon-orange bg-neon-orange/10 p-4 space-y-3"
          >
            <p className="font-mono text-xs text-neon-orange uppercase tracking-widest font-bold">
              <AlertTriangle size={12} className="inline mr-1.5" />
              Replace your edits?
            </p>
            <p className="text-slate-400 text-xs">You have unsaved edits. Regenerating will replace them.</p>
            <div className="flex gap-2">
              <button
                onClick={() => { setConfirmRegen(false); generate(tone); }}
                className="flex-1 py-2 bg-neon-orange text-surface-900 font-mono text-xs font-black uppercase tracking-widest"
              >
                Replace
              </button>
              <button
                onClick={() => setConfirmRegen(false)}
                className="flex-1 py-2 border-2 border-border text-slate-400 font-mono text-xs uppercase tracking-widest hover:text-white"
              >
                Keep Edits
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default ProposalPanel;
