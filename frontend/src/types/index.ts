/**
 * FreelanceIQ — TypeScript Types
 * Phase 1 API Contract — LOCKED
 * Any change to this file requires alignment between Musa (backend) and Omer (frontend).
 */

// ── Primitive enums ──────────────────────────────────────────────────────────

export type SubscriptionTier = "free" | "pro" | "enterprise";
export type UserRole = "freelancer" | "admin";
export type ExperienceLevel = "junior" | "mid" | "senior" | "expert";
export type QualityTier = "high" | "medium" | "risky" | "avoid";
export type BudgetType = "fixed" | "hourly";
export type ProposalStatus = "drafted" | "sent" | "viewed" | "replied" | "interview" | "won" | "lost";
export type ParsingStatus = "pending" | "processing" | "done" | "failed";
export type CoverLetterStyle = "professional" | "casual" | "technical" | "creative";
export type BidStrategy = "Competitive" | "Value" | "Premium";
export type ProposalTier = "low" | "medium" | "high" | "very_high";

// ── Core entities ────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  role: UserRole;
  subscription_tier: SubscriptionTier;
  created_at: string;
}

export interface Skill {
  name: string;
  level: "beginner" | "intermediate" | "advanced" | "expert";
  years: number;
}

export interface FreelancerProfile {
  id: string;
  headline?: string;
  summary?: string;
  skills?: Skill[];
  experience_level?: ExperienceLevel;
  niche?: string;
  specializations?: string[];
  communication_tone?: string;
  inferred_hourly_rate_min?: number;
  inferred_hourly_rate_max?: number;
  preferred_project_types?: string[];
  preferred_industries?: string[];
  last_analyzed_at?: string;
}

export interface Client {
  id: string;
  country?: string;
  payment_verified: boolean;
  total_spent?: number;
  hire_rate?: number;
  total_hires: number;
  average_rating?: number;
  quality_tier?: QualityTier;
  quality_score?: number;
  trust_score?: number;
  red_flags?: string[];
  green_flags?: string[];
}

// ── Phase 1: Score signals object ────────────────────────────────────────────

export interface JobScore {
  /** Deterministic client quality score (0.0 – 1.0). Null if job hasn't been scored yet. */
  client_quality: number | null;
}

// ── Phase 1: Bid recommendation object ──────────────────────────────────────

export interface BidRecommendation {
  /** Mid-point of the acceptable bid range, pre-computed for display */
  recommended:  number | null;
  range_min:    number | null;
  range_max:    number | null;
  /** Human-readable range string e.g. "$130.00 – $159.50 acceptable range" */
  range:        string | null;
  strategy:     BidStrategy | null;
  rationale:    string | null;
  /** Win confidence float 0.0 – 1.0 */
  confidence:   number | null;
}

// ── Job — Phase 1 locked shape ───────────────────────────────────────────────

export interface Job {
  // ── Original fields (never removed) ──────────────────────────────────────
  id: string;
  upwork_job_id: string;
  title: string;
  description?: string;
  url?: string;
  budget_type?: BudgetType;
  budget_min?: number;
  budget_max?: number;
  hourly_rate_min?: number;
  hourly_rate_max?: number;
  required_skills?: string[];
  experience_level?: string;
  project_length?: string;
  proposal_count: number;
  proposal_tier?: ProposalTier;
  posted_at?: string;
  scraped_at: string;
  client?: Client;

  // ── Phase 1 additions ─────────────────────────────────────────────────────
  /** Score signals. Present after the job has been processed by the scoring engine. */
  score?: JobScore | null;
  /** Full bid recommendation. Null when job hasn't been scored yet. */
  bid?: BidRecommendation | null;
}

// ── Match score (from /matches endpoint) ────────────────────────────────────

export interface MatchScore {
  id: string;
  overall_score: number;
  confidence_score?: number;
  skill_match_score?: number;
  semantic_relevance_score?: number;
  competition_score?: number;
  client_quality_score?: number;
  budget_fit_score?: number;
  win_probability?: number;
  strengths?: string[];
  weaknesses?: string[];
  recommended_approach?: string;
  ai_explanation?: string;
  scored_at: string;
}

export interface JobMatch {
  match: MatchScore;
  job: Job;
}

// ── Cover Letter & Proposal ──────────────────────────────────────────────────

export interface CoverLetter {
  id: string;
  job_id: string;
  content: string;
  style: CoverLetterStyle;
  variant_index: number;
  is_edited: boolean;
  is_sent: boolean;
  token_count?: number;
  created_at: string;
}

export interface Proposal {
  id: string;
  job_id: string;
  status: ProposalStatus;
  bid_amount?: number;
  bid_type?: BudgetType;
  sent_at?: string;
  outcome_value?: number;
  created_at: string;
}

// ── Alert & Config ───────────────────────────────────────────────────────────

export interface AlertConfig {
  min_match_score: number;
  max_proposal_count: number;
  max_hours_since_posted: number;
  min_client_quality_score: number;
  notify_slack: boolean;
  notify_email: boolean;
  notify_push: boolean;
  is_active: boolean;
}

export interface AlertEvent {
  id: string;
  job_id: string;
  trigger_reason?: string;
  channel: string;
  sent_at: string;
  read_at?: string;
  is_actioned: boolean;
}

// ── Analytics (legacy) ───────────────────────────────────────────────────────

export interface ProposalAnalytics {
  total: number;
  sent: number;
  replied: number;
  won: number;
  lost: number;
  win_rate: number;
  response_rate: number;
  total_revenue: number;
  avg_project_value: number;
}

export interface ScrapingStats {
  total_jobs: number;
  active_jobs: number;
  recent_runs: Array<{
    id: string;
    status: string;
    jobs_scraped: number;
    jobs_new: number;
    started_at: string;
    duration_seconds: number;
  }>;
}

// ── Phase 2 stubs (field names locked, details filled in Phase 2) ────────────

export interface ScrapeStatus {
  is_running:  boolean;
  last_run: {
    status:      string;
    jobs_found:  number;
    jobs_new:    number;
    completed_at: string;
    error_message?: string;
  } | null;
  next_run_at: string | null;
}

export interface Notification {
  id:         string;
  job_id:     string;
  job_title:  string;
  score:      number;
  message:    string;
  is_read:    boolean;
  created_at: string;
}

// ── Phase 3 stub ─────────────────────────────────────────────────────────────

export interface CVProfile {
  id:                   string;
  name?:                string;
  title?:               string;
  skills:               string[];
  experience_level?:    ExperienceLevel;
  target_hourly_rate?:  number;
  target_fixed_min?:    number;
  target_fixed_max?:    number;
  profile_confirmed?:   boolean;
}

// ── Phase 4 stub ─────────────────────────────────────────────────────────────

export interface AnalyticsData {
  jobs_scraped_total:   number;
  jobs_scraped_today:   number;
  avg_overall_score:    number;
  high_match_count:     number;
  score_distribution:   { label: string; count: number }[];
  avg_budget_min:       number | null;
  avg_budget_max:       number | null;
  avg_proposals_count:  number | null;
  top_skills_in_demand: { skill: string; count: number }[];
  scrape_history:       { date: string; jobs_found: number; jobs_new: number }[];
  proposals_generated:  number;
  alerts_sent:          number;
}

