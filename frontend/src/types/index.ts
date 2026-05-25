// ─────────────────────────────────────────────────────────────────────────────
// FreelanceIQ — API Type Contract
// Phase 1: Job, Client, Score, Bid types locked.
// Phase 2+: ScrapeStatus, Notification stubs.
// Phase 3+: CVProfile stub.
// Phase 4+: AnalyticsData stub.
// NO `any` types allowed anywhere in this file.
// ─────────────────────────────────────────────────────────────────────────────

// ── Enums / Literals ──────────────────────────────────────────────────────────

export type BudgetType         = "fixed" | "hourly";
export type ProposalTier       = "low" | "medium" | "high" | "very_high";
export type BidStrategy        = "Competitive" | "Value" | "Premium";
export type UserRole           = "admin" | "user";
export type SubscriptionTier   = "free" | "pro" | "enterprise";
export type ExperienceLevel    = "entry" | "intermediate" | "expert";
export type CoverLetterStyle   = "formal" | "conversational" | "technical" | "brief";
export type ProposalStatus     = "drafted" | "sent" | "replied" | "interview" | "won" | "lost";
export type QualityTier        = "high" | "medium" | "risky" | "avoid";

// ── Phase 1: Score sub-object ─────────────────────────────────────────────────
// All values normalised to 0.0–1.0 by the API.
// client_quality is always present (computed at ingestion).
// overall, skill_match, roi, competition are null until the user scores the job.

export interface JobScore {
  /** Weighted aggregate score 0.0-1.0 */
  overall?: number | null;
  /** Skill match score 0.0-1.0 (from MatchScore) */
  skill_match?: number | null;
  /** Semantic relevance / ROI score 0.0-1.0 (from MatchScore) */
  roi?: number | null;
  /** Competition score 0.0-1.0 (from MatchScore) */
  competition?: number | null;
  /** Client quality score 0.0-1.0 (hire_rate 40%, avg_rating 40%, jobs_posted 20%) */
  client_quality?: number | null;
}

// ── Phase 1: Bid sub-object ───────────────────────────────────────────────────

export interface BidRecommendation {
  /** Recommended bid amount in the job currency */
  recommended?: number | null;
  range_min?: number | null;
  range_max?: number | null;
  /** Human-readable range string, e.g. "$85.50 – $104.50 acceptable range" */
  range?: string | null;
  strategy?: BidStrategy | null;
  rationale?: string | null;
  /** Win confidence 0.0-1.0 */
  confidence?: number | null;
}

// ── Phase 2 stubs (filled in Phase 2) ────────────────────────────────────────

export interface ScrapeStatus {
  last_run: {
    id: string;
    status: string;
    jobs_found: number;
    jobs_new: number;
    started_at: string;
    completed_at?: string;
    error_message?: string;
  } | null;
  next_run_at?: string | null;
  is_running: boolean;
}

// ── Phase 2: Notification (in-app alert) ─────────────────────────────────────

export interface Notification {
  id: string;
  job_id?: string | null;
  job_title: string;
  /** Aggregate match score 0-100 integer (matches backend Integer column) */
  score: number;
  message?: string | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationsResponse {
  unread_count: number;
  notifications: Notification[];
}

// ── Phase 2: Alert config (user preferences) ─────────────────────────────────

export interface AlertConfigPhase2 {
  score_threshold: number;   // 0.0–1.0
  slack_webhook_url?: string | null;
  email_address?: string | null;
  enabled: boolean;
}

// ── Phase 3 stub ──────────────────────────────────────────────────────────────

export interface CVProfile {
  id: string;
  headline?: string;
  summary?: string;
  skills?: { name: string; level: string; years: number }[];
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

// ── Phase 4 stub ──────────────────────────────────────────────────────────────

export interface AnalyticsData {
  win_rate:             number;
  response_rate:        number;
  total_revenue:        number;
  avg_project_value:    number;
  proposals_by_month:   { month: string; count: number; won: number }[];
  top_skill_matches:    { skill: string; match_rate: number }[];
  scrape_history:       { date: string; jobs_found: number; jobs_new: number }[];
  proposals_generated:  number;
  alerts_sent:          number;
}

// ── Domain models ─────────────────────────────────────────────────────────────

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

// ── Job — Phase 1 locked ──────────────────────────────────────────────────────

export interface Job {
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
  /** Phase 1: scoring sub-object */
  score?: JobScore | null;
  /** Phase 1: bid recommendation sub-object */
  bid?: BidRecommendation | null;
}

export interface MatchScore {
  id: string;
  overall_score: number;
  confidence_score?: number;
  skill_match_score?: number;
  semantic_relevance_score?: number;
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
