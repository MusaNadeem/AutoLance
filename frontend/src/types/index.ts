/**
 * FreelanceRadar — TypeScript Types
 */

export type SubscriptionTier = "free" | "pro" | "enterprise";
export type UserRole = "freelancer" | "admin";
export type ExperienceLevel = "junior" | "mid" | "senior" | "expert";
export type QualityTier = "high" | "medium" | "risky" | "avoid";
export type BudgetType = "fixed" | "hourly";
export type ProposalStatus = "drafted" | "sent" | "viewed" | "replied" | "interview" | "won" | "lost";
export type ParsingStatus = "pending" | "processing" | "done" | "failed";
export type CoverLetterStyle = "professional" | "casual" | "technical" | "creative";

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
  proposal_tier?: "low" | "medium" | "high" | "very_high";
  posted_at?: string;
  scraped_at: string;
  client?: Client;
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
