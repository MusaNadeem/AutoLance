/**
 * FreelanceRadar API Client
 * Typed HTTP client for all backend endpoints
 */

import axios, { AxiosInstance } from "axios";

const CONFIGURED_API_URL = process.env.NEXT_PUBLIC_API_URL;

// For client-side requests, `backend` is not resolvable from the user's browser.
// Default to:
// - `http://localhost:8000` when running Next directly on :3000
// - current origin when behind nginx on :80 (so `/api/v1` is proxied)
const API_URL =
  CONFIGURED_API_URL ||
  (typeof window !== "undefined"
    ? (window.location.port === "3000"
        ? "http://localhost:8000"
        : window.location.origin)
    : "http://backend:8000");

export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// ── Request interceptor: inject auth token ────────────────
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ── Response interceptor: handle 401 refresh ─────────────
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Clear tokens and redirect to login
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ── Auth ─────────────────────────────────────────────────
export const auth = {
  register: (data: { email: string; password: string; full_name: string }) =>
    apiClient.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    apiClient.post("/auth/login", data),
  me: () => apiClient.get("/auth/me"),
  refresh: (token: string) => apiClient.post("/auth/refresh", { refresh_token: token }),
};

// ── CV ─────────────────────────────────────────────────
export const cv = {
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return apiClient.post("/cv/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  list: () => apiClient.get("/cv/"),
  get: (id: string) => apiClient.get(`/cv/${id}`),
};

// ── Jobs ─────────────────────────────────────────────────
export const jobs = {
  list: (params?: {
    page?: number;
    limit?: number;
    budget_type?: string;
    experience_level?: string;
    proposal_tier?: string;
  }) => apiClient.get("/jobs/", { params }),
  get: (id: string) => apiClient.get(`/jobs/${id}`),
  triggerScrape: () => apiClient.post("/jobs/trigger-scrape"),
  stats: () => apiClient.get("/jobs/stats"),
};

// ── Matches ───────────────────────────────────────────────
export const matches = {
  list: (params?: { min_score?: number; page?: number }) =>
    apiClient.get("/matches/", { params }),
  score: (jobId: string) => apiClient.post(`/matches/${jobId}/score`),
};

// ── Cover Letters ─────────────────────────────────────────
export const coverLetters = {
  generate: (data: { job_id: string; style?: string; custom_instructions?: string }) =>
    apiClient.post("/cover-letters/generate", data),
  list: () => apiClient.get("/cover-letters/"),
  update: (id: string, content: string) =>
    apiClient.patch(`/cover-letters/${id}`, { content }),
};

// ── Proposals ─────────────────────────────────────────────
export const proposals = {
  create: (data: { job_id: string; cover_letter_id?: string; bid_amount?: number }) =>
    apiClient.post("/proposals/", data),
  list: (status?: string) => apiClient.get("/proposals/", { params: { status } }),
  updateStatus: (id: string, status: string, outcome_value?: number) =>
    apiClient.patch(`/proposals/${id}/status`, { status, outcome_value }),
  analytics: () => apiClient.get("/proposals/analytics"),
};

// ── Alerts ─────────────────────────────────────────────────
export const alerts = {
  getConfig: () => apiClient.get("/alerts/config"),
  updateConfig: (data: object) => apiClient.put("/alerts/config", data),
  events: () => apiClient.get("/alerts/events"),
};

// ── SWR Fetcher ──────────────────────────────────────────
export const fetcher = (url: string) => apiClient.get(url).then((res) => res.data);

