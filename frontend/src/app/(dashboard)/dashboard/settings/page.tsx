"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { User, Key, Trash2, Save, Check, Loader2, AlertTriangle } from "lucide-react";
import useSWR from "swr";
import { settings } from "@/lib/api";

export default function SettingsPage() {
  const { data: userData } = useSWR(
    "/settings",
    () => settings.get().then((r) => r.data),
    { revalidateOnFocus: false }
  );

  const [profile, setProfile] = useState({ full_name: "", email: "" });
  const [password, setPassword] = useState({ current: "", new: "", confirm: "" });
  const [profileStatus, setProfileStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [passwordStatus, setPasswordStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  useEffect(() => {
    if (userData) {
      setProfile({
        full_name: userData.full_name ?? "",
        email:     userData.email ?? "",
      });
    }
  }, [userData]);

  const handleSaveProfile = async () => {
    setProfileStatus("saving");
    try {
      await settings.updateProfile({ full_name: profile.full_name });
      setProfileStatus("saved");
      setTimeout(() => setProfileStatus("idle"), 2500);
    } catch {
      setProfileStatus("error");
      setTimeout(() => setProfileStatus("idle"), 3000);
    }
  };

  const handleChangePassword = async () => {
    setPasswordError(null);
    if (password.new !== password.confirm) {
      setPasswordError("New passwords don't match");
      return;
    }
    if (password.new.length < 8) {
      setPasswordError("Password must be at least 8 characters");
      return;
    }
    setPasswordStatus("saving");
    try {
      await settings.changePassword({
        current_password: password.current,
        new_password:     password.new,
      });
      setPasswordStatus("saved");
      setPassword({ current: "", new: "", confirm: "" });
      setTimeout(() => setPasswordStatus("idle"), 2500);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setPasswordError(err?.response?.data?.detail ?? "Failed to update password");
      setPasswordStatus("error");
      setTimeout(() => setPasswordStatus("idle"), 3000);
    }
  };

  const handleDeleteAccount = async () => {
    try {
      await settings.deleteAccount();
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/login";
    } catch {
      // silently fail — user can retry
    }
  };

  return (
    <div className="p-6 space-y-8 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-slate-400 mt-1">Manage your account and preferences</p>
      </div>

      {/* Profile */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6 space-y-5">
        <h2 className="font-semibold text-white flex items-center gap-2">
          <User size={16} className="text-brand-400" /> Profile
        </h2>
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-brand flex items-center justify-center text-white font-bold text-xl">
            {(profile.full_name || "?").charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="text-white font-medium">{profile.full_name || "—"}</p>
            <p className="text-slate-400 text-sm">{profile.email}</p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Full Name</label>
            <input
              value={profile.full_name}
              onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
              className="w-full bg-surface-4 border border-surface-5 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Email</label>
            <input
              value={profile.email}
              disabled
              className="w-full bg-surface-4 border border-surface-5 rounded-xl px-4 py-2.5 text-slate-500 text-sm cursor-not-allowed"
            />
          </div>
        </div>
        <button
          onClick={handleSaveProfile}
          disabled={profileStatus === "saving"}
          className="btn-primary flex items-center gap-2 text-sm py-2.5 px-5 disabled:opacity-60"
        >
          {profileStatus === "saving" ? (
            <><Loader2 size={14} className="animate-spin" /> Saving...</>
          ) : profileStatus === "saved" ? (
            <><Check size={14} /> Saved!</>
          ) : profileStatus === "error" ? (
            <><AlertTriangle size={14} /> Error</>
          ) : (
            <><Save size={14} /> Save Changes</>
          )}
        </button>
      </motion.div>

      {/* Change Password */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-6 space-y-4">
        <h2 className="font-semibold text-white flex items-center gap-2">
          <Key size={16} className="text-violet-400" /> Change Password
        </h2>
        {passwordError && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            <AlertTriangle size={14} /> {passwordError}
          </div>
        )}
        {(["current", "new", "confirm"] as const).map((field) => (
          <div key={field}>
            <label className="block text-sm font-medium text-slate-300 mb-2 capitalize">
              {field === "confirm" ? "Confirm New" : field === "new" ? "New" : "Current"} Password
            </label>
            <input
              type="password"
              value={password[field]}
              onChange={(e) => {
                setPassword({ ...password, [field]: e.target.value });
                setPasswordError(null);
              }}
              placeholder="••••••••"
              className="w-full bg-surface-4 border border-surface-5 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 text-sm"
            />
          </div>
        ))}
        <button
          onClick={handleChangePassword}
          disabled={passwordStatus === "saving" || !password.current || !password.new || !password.confirm}
          className="btn-ghost flex items-center gap-2 text-sm py-2.5 px-5 disabled:opacity-60"
        >
          {passwordStatus === "saving" ? (
            <><Loader2 size={14} className="animate-spin" /> Updating...</>
          ) : passwordStatus === "saved" ? (
            <><Check size={14} /> Updated!</>
          ) : (
            <><Key size={14} /> Update Password</>
          )}
        </button>
      </motion.div>

      {/* Plan & Billing */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-6">
        <h2 className="font-semibold text-white mb-4">Plan & Billing</h2>
        <div className="flex items-center justify-between p-4 rounded-xl bg-surface-4 border border-surface-5 mb-4">
          <div>
            <p className="text-white font-medium capitalize">
              {userData?.subscription_tier ?? "free"} Plan
            </p>
            <p className="text-slate-400 text-sm">50 matches/day · Basic alerts</p>
          </div>
          <span className="px-3 py-1 rounded-full bg-surface-5 text-slate-300 text-xs font-medium">Current</span>
        </div>
        <button className="btn-primary text-sm py-2.5 px-5">Upgrade to Pro →</button>
      </motion.div>

      {/* Danger Zone */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card p-6 border border-red-500/20">
        <h2 className="font-semibold text-white mb-2 flex items-center gap-2">
          <Trash2 size={16} className="text-red-400" /> Danger Zone
        </h2>
        <p className="text-slate-400 text-sm mb-4">Permanently delete your account and all data. This cannot be undone.</p>

        {!deleteConfirm ? (
          <button
            onClick={() => setDeleteConfirm(true)}
            className="bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 rounded-xl px-5 py-2.5 text-sm font-medium transition-colors"
          >
            Delete Account
          </button>
        ) : (
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-400">Are you sure?</span>
            <button
              onClick={handleDeleteAccount}
              className="bg-red-500 text-white rounded-xl px-4 py-2 text-sm font-semibold hover:bg-red-600 transition-colors"
            >
              Yes, delete
            </button>
            <button
              onClick={() => setDeleteConfirm(false)}
              className="text-slate-400 hover:text-white text-sm transition-colors px-4 py-2"
            >
              Cancel
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
}
