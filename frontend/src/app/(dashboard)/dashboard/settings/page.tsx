"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { User, Key, Trash2, Save, Check } from "lucide-react";

export default function SettingsPage() {
  const [saved, setSaved] = useState<string | null>(null);
  const [profile, setProfile] = useState({ name: "Alex Johnson", email: "alex@example.com", avatar: "" });
  const [password, setPassword] = useState<{ current: string; new: string; confirm: string }>({ current: "", new: "", confirm: "" });

  const save = (section: string) => {
    setSaved(section);
    setTimeout(() => setSaved(null), 2000);
  };

  return (
    <div className="p-6 space-y-8 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-slate-400 mt-1">Manage your account and preferences</p>
      </div>

      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6 space-y-5">
        <h2 className="font-semibold text-white flex items-center gap-2"><User size={16} className="text-brand-400" /> Profile</h2>
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-brand flex items-center justify-center text-white font-bold text-xl">
            {profile.name.charAt(0)}
          </div>
          <div>
            <p className="text-white font-medium">{profile.name}</p>
            <p className="text-slate-400 text-sm">{profile.email}</p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Full Name</label>
            <input value={profile.name} onChange={(e) => setProfile({ ...profile, name: e.target.value })}
              className="w-full bg-surface-4 border border-surface-5 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Email</label>
            <input value={profile.email} onChange={(e) => setProfile({ ...profile, email: e.target.value })}
              className="w-full bg-surface-4 border border-surface-5 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 text-sm" />
          </div>
        </div>
        <button onClick={() => save("profile")} className="btn-primary flex items-center gap-2 text-sm py-2.5 px-5">
          {saved === "profile" ? <><Check size={14} /> Saved!</> : <><Save size={14} /> Save Changes</>}
        </button>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-6 space-y-4">
        <h2 className="font-semibold text-white flex items-center gap-2"><Key size={16} className="text-violet-400" /> Change Password</h2>
        {(["current", "new", "confirm"] as const).map((field) => (
          <div key={field}>
            <label className="block text-sm font-medium text-slate-300 mb-2 capitalize">{field.replace("_", " ")} Password</label>
            <input type="password" value={password[field]}
              onChange={(e) => setPassword({ ...password, [field]: e.target.value })}
              placeholder="••••••••"
              className="w-full bg-surface-4 border border-surface-5 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 text-sm" />
          </div>
        ))}
        <button onClick={() => save("password")} className="btn-ghost flex items-center gap-2 text-sm py-2.5 px-5">
          {saved === "password" ? <><Check size={14} /> Updated!</> : <><Key size={14} /> Update Password</>}
        </button>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-6">
        <h2 className="font-semibold text-white mb-4">Plan & Billing</h2>
        <div className="flex items-center justify-between p-4 rounded-xl bg-surface-4 border border-surface-5 mb-4">
          <div>
            <p className="text-white font-medium">Free Plan</p>
            <p className="text-slate-400 text-sm">50 matches/day · Basic alerts</p>
          </div>
          <span className="px-3 py-1 rounded-full bg-surface-5 text-slate-300 text-xs font-medium">Current</span>
        </div>
        <button className="btn-primary text-sm py-2.5 px-5">Upgrade to Pro →</button>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card p-6 border border-red-500/20">
        <h2 className="font-semibold text-white mb-2 flex items-center gap-2"><Trash2 size={16} className="text-red-400" /> Danger Zone</h2>
        <p className="text-slate-400 text-sm mb-4">Permanently delete your account and all data.</p>
        <button className="bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 rounded-xl px-5 py-2.5 text-sm font-medium transition-colors">
          Delete Account
        </button>
      </motion.div>
    </div>
  );
}
