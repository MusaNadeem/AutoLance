/**
 * FreelanceIQ API Client — Phase 1
 * All components call this file. Never raw fetch() in a component.
 */

import axios, { AxiosInstance } from "axios";
import type {
  Job,
  Client,
  ScrapeStatus,
  Notification,
  AnalyticsData,
  CVProfile,
} from "@/types";

const CONFIGURED_API_URL = process.env.NEXT_PUBLIC_API_URL;

const API_URL =
  CONFIGURED_API_URL ||
  (typeof window !== "undefined"
    ? window.location.port === "3000"
      ? "http://localhost:8000"
      : window.location.origin
    : "http://backend:8000");

export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export const auth = {
  register: (data: { email: string; password: string; full_name: string }) =>
    apiClient.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    apiClient.post("/auth/login", data),
  me: () => apiClient.get("/auth/me"),
  refresh: (token: string) =>
    apiClient.post("/auth/refresh", { refresh_token: token }),
};

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

// Phase 1 LIVE
export const jobs = {
  list: (params?: {
    page?: number;
    limit?: number;
    budget_type?: string;
    experience_level?: string;
    proposal_tier?: string;
  }) => apiClient.get<{ jobs: Job[] }>("/jobs/", { params }),
  get: (id: string) => apiClient.get<Job & { client?: Client }>(`/jobs/${id}`),
  triggerScrape: () => apiClient.post("/jobs/trigger-scrape"),
  stats: () => apiClient.get("/jobs/stats"),
};

export const matches = {
  list: (params?: { min_score?: number; page?: number }) =>
    apiClient.get("/matches/", { params }),
  score: (jobId: string) => apiClient.post(`/matches/${jobId}/score`),
};

export const coverLetters = {
  generate: (data: {
    job_id: string;
    style?: string;
    custom_instructions?: string;
  }) => apiClient.post("/cover-letters/generate", data),
  list: () => apiClient.get("/cover-letters/"),
  update: (id: string, content: string) =>
    apiClient.patch(`/cover-letters/${id}`, { content }),
};

export const proposals = {
  create: (data: {
    job_id: string;
    cover_letter_id?: string;
    bid_amount?: number;
  }) => apiClient.post("/proposals/", data),
  list: (status?: string) =>
    apiClient.get("/proposals/", { params: { status } }),
  updateStatus: (id: string, status: string, outcome_value?: number) =>
    apiClient.patch(`/proposals/${id}/status`, { status, outcome_value }),
  analytics: () => apiClient.get("/proposals/analytics"),
};

export const alerts = {
  getConfig: () => apiClient.get("/alerts/config"),
  updateConfig: (data: object) => apiClient.put("/alerts/config", data),
  events: () => apiClient.get("/alerts/events"),
};

// Phase 2 stubs
export const scrape = {
  status: () => apiClient.get<ScrapeStatus>("/scrape/status"),
  trigger: () => apiClient.post<{ task_id: string }>("/scrape/trigger"),
};

export const notifications = {
  list: () => apiClient.get<Notification[]>("/alerts"),
  readAll: () => apiClient.post("/alerts/read-all"),
  read: (id: string) => apiClient.post(`/alerts/read/${id}`),
};

// Phase 4 stub
export const analytics = {
  get: () => apiClient.get<AnalyticsData>("/analytics"),
};

// Phase 3 stub
export const cvProfile = {
  get: () => apiClient.get<CVProfile>("/cv/profile"),
  update: (data: Partial<CVProfile>) =>
    apiClient.put<CVProfile>("/cv/profile", data),
};

export const fetcher = (url: string) =>
  apiClient.get(url).then((res) => res.data);
