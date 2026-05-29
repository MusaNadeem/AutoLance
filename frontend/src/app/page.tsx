"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Target, Zap, Shield, BarChart3, Bell, FileText,
  ArrowRight
} from "lucide-react";

const features = [
  {
    icon: Target,
    title: "AI Match Scoring",
    description: "Claude scores every job 0–100 against your profile with win probability and reasoning across 10 dimensions.",
    color: "bg-neon-lime text-surface-900",
  },
  {
    icon: Shield,
    title: "Client Quality Detector",
    description: "Instantly identify high-quality vs risky clients. Red flags, green flags, and trust scores before you apply.",
    color: "bg-neon-cyan text-surface-900",
  },
  {
    icon: FileText,
    title: "AI Cover Letters",
    description: "Personalized, human-sounding cover letters generated in seconds. Multiple style variants. One-click generation.",
    color: "bg-neon-pink text-surface-900",
  },
  {
    icon: Bell,
    title: "Real-Time Alerts",
    description: "Get notified the moment a high-match job appears. Slack, email, and push notifications with configurable thresholds.",
    color: "bg-neon-orange text-surface-900",
  },
  {
    icon: BarChart3,
    title: "Proposal Analytics",
    description: "Track win rates, response rates, ROI, and category performance with a full proposal lifecycle tracker.",
    color: "bg-neon-cyan text-surface-900",
  },
  {
    icon: Zap,
    title: "Easy-Win Radar",
    description: "Surface low-competition opportunities posted under 2 hours ago. Be first. Win more.",
    color: "bg-neon-lime text-surface-900",
  },
];

const stats = [
  { label: "JOBS SCRAPED DAILY", value: "50K+" },
  { label: "MATCH SCORE LIFT", value: "3.2X" },
  { label: "TIME SAVED/WK", value: "8H" },
  { label: "WIN RATE LIFT", value: "67%" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-grid-pattern relative">
      {/* Navigation */}
      <nav className="fixed top-0 inset-x-0 z-50 border-b-2 border-border bg-surface-900/95 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 border-2 border-border bg-neon-lime flex items-center justify-center shadow-[4px_4px_0px_0px_rgba(46,46,46,1)] hover:shadow-[2px_2px_0px_0px_rgba(46,46,46,1)] hover:translate-x-[2px] hover:translate-y-[2px] transition-all cursor-pointer">
              <Target className="w-6 h-6 text-surface-900" strokeWidth={2.5} />
            </div>
            <span className="font-display font-bold text-xl text-white uppercase tracking-wider">AutoLance</span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-slate-400 font-mono font-bold uppercase text-sm hover:text-neon-lime transition-colors">Features</a>
            <a href="#how-it-works" className="text-slate-400 font-mono font-bold uppercase text-sm hover:text-neon-lime transition-colors">How it works</a>
            <a href="#pricing" className="text-slate-400 font-mono font-bold uppercase text-sm hover:text-neon-lime transition-colors">Pricing</a>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-slate-300 font-mono font-bold uppercase text-sm hover:text-white transition-colors">
              Sign in
            </Link>
            <Link href="/register" className="btn-primary text-sm py-2 px-6">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-40 pb-24 px-6 relative">
        {/* Decorative elements */}
        <div className="absolute top-1/4 left-10 w-24 h-24 border-4 border-neon-cyan/20 rounded-full blur-sm animate-pulse" />
        <div className="absolute top-1/3 right-10 w-32 h-32 border-4 border-neon-pink/20 blur-sm animate-pulse" style={{ animationDelay: '1s' }} />

        <div className="max-w-5xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 border-2 border-border bg-surface-800 text-slate-300 font-mono font-bold text-xs uppercase tracking-wider mb-8">
              <Zap className="w-4 h-4 text-neon-lime" strokeWidth={2.5} />
              Powered by Claude AI + Bright Data
            </div>

            <h1 className="text-6xl md:text-8xl font-display font-bold text-white leading-none tracking-tighter mb-8 uppercase">
              Win more Upwork jobs <br className="hidden md:block" />
              <span className="text-neon-lime relative inline-block">
                with AI intelligence
                <div className="absolute -bottom-2 left-0 right-0 h-2 bg-neon-lime/20" />
              </span>
            </h1>

            <p className="text-xl md:text-2xl text-slate-400 max-w-3xl mx-auto mb-12 leading-relaxed font-sans">
              AutoLance scrapes Upwork in real time, analyzes your CV with Claude,
              and surfaces your highest-converting opportunities with match scores,
              client quality signals, and personalized cover letters — instantly.
            </p>

            <div className="flex flex-col sm:flex-row gap-6 justify-center">
              <Link href="/register" className="btn-primary flex items-center gap-2 justify-center text-lg py-5 px-10">
                START FOR FREE
                <ArrowRight className="w-6 h-6" strokeWidth={2.5} />
              </Link>
              <Link href="/dashboard" className="btn-ghost flex items-center gap-2 justify-center text-lg py-5 px-10">
                VIEW DEMO
              </Link>
            </div>
          </motion.div>

          {/* Stats bar */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2, ease: "easeOut" }}
            className="mt-24 grid grid-cols-2 md:grid-cols-4 gap-6"
          >
            {stats.map((stat, i) => (
              <div key={stat.label} className={`brutal-panel p-6 text-center ${i % 2 === 0 ? "border-neon-cyan" : "border-neon-pink"}`}>
                <div className="text-4xl md:text-5xl font-display font-bold text-white mb-2">{stat.value}</div>
                <div className="text-xs font-mono font-bold text-slate-400 tracking-widest">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-32 px-6 bg-surface-800 border-y-2 border-border relative">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-5xl md:text-6xl font-display font-bold text-white uppercase tracking-tighter mb-6">
              Everything you need to win
            </h2>
            <p className="text-slate-400 text-xl max-w-2xl mx-auto">
              A complete intelligence system built for serious freelancers who want
              to spend less time searching and more time earning.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
                className="brutal-panel p-8 group relative overflow-hidden"
              >
                <div className={`absolute top-0 right-0 w-24 h-24 opacity-10 rounded-bl-[100px] ${feature.color.split(" ")[0]} transition-all group-hover:scale-150 duration-500`} />
                <div className={`w-14 h-14 border-2 border-surface-900 flex items-center justify-center mb-6 shadow-brutal-sm group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform ${feature.color}`}>
                  <feature.icon className="w-7 h-7" strokeWidth={2.5} />
                </div>
                <h3 className="text-2xl font-display font-bold text-white mb-4 uppercase tracking-wide">{feature.title}</h3>
                <p className="text-slate-400 text-base leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-32 px-6 bg-surface-900 relative">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-5xl md:text-6xl font-display font-bold text-white uppercase tracking-tighter mb-4">How it works</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8 relative">
            {/* Connecting line for desktop */}
            <div className="hidden md:block absolute top-12 left-[10%] right-[10%] h-1 bg-border z-0" />
            
            {[
              { step: "01", title: "Upload your CV", desc: "Upload your resume or portfolio. Claude extracts your skills, niche, experience, and builds your intelligence profile.", color: "text-neon-cyan" },
              { step: "02", title: "Jobs scraped 24/7", desc: "Bright Data scrapes Upwork every 15 minutes. Every job is scored against your profile across 10 AI dimensions.", color: "text-neon-lime" },
              { step: "03", title: "Apply with confidence", desc: "View ranked matches, read the AI explanation, generate your cover letter, and track every proposal to close.", color: "text-neon-pink" },
            ].map((item) => (
              <div key={item.step} className="relative z-10 brutal-panel p-8 text-center bg-surface-800">
                <div className={`w-24 h-24 mx-auto border-4 border-surface-900 bg-surface-800 flex items-center justify-center rounded-full mb-8 shadow-brutal-md ${item.color}`}>
                  <div className="text-4xl font-display font-bold tracking-tighter">{item.step}</div>
                </div>
                <h3 className="text-2xl font-display font-bold text-white mb-4 uppercase tracking-wide">{item.title}</h3>
                <p className="text-slate-400 text-base leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-32 px-6 bg-surface-800 border-y-2 border-border">
        <div className="max-w-4xl mx-auto text-center">
          <div className="border-4 border-neon-lime bg-surface-900 p-16 shadow-[16px_16px_0px_0px_rgba(204,255,0,0.2)]">
            <h2 className="text-5xl md:text-6xl font-display font-bold text-white mb-6 uppercase tracking-tighter">
              Ready to win more contracts?
            </h2>
            <p className="text-slate-400 text-xl mb-12 max-w-2xl mx-auto">
              Join freelancers using AI to find and win their best jobs. Stop scrolling, start closing.
            </p>
            <Link href="/register" className="btn-primary inline-flex items-center gap-3 text-xl py-6 px-12">
              GET STARTED &mdash; IT&apos;S FREE
              <ArrowRight className="w-6 h-6" strokeWidth={2.5} />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t-2 border-border py-12 px-6 bg-surface-900">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 border-2 border-border bg-neon-lime flex items-center justify-center">
              <Target className="w-4 h-4 text-surface-900" strokeWidth={3} />
            </div>
            <span className="font-display font-bold text-white text-lg uppercase tracking-wider">AutoLance</span>
          </div>
          <p className="text-slate-500 font-mono text-sm uppercase tracking-widest font-bold">
            © 2026 AutoLance. Built with Claude + Bright Data.
          </p>
        </div>
      </footer>
    </div>
  );
}
