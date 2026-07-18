const BASE = "/api";

function getApiKey(): string | null {
  return localStorage.getItem("jobposting_api_key");
}

export function setApiKey(key: string | null) {
  if (key) localStorage.setItem("jobposting_api_key", key);
  else localStorage.removeItem("jobposting_api_key");
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string> | undefined),
  };
  const apiKey = getApiKey();
  if (apiKey) headers["X-API-Key"] = apiKey;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      try {
        detail = await res.text();
      } catch {
        /* ignore */
      }
    }
    throw new Error(detail || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface Source {
  id: number;
  name: string;
  kind: string;
  base_url: string;
  enabled: boolean;
  scrape_interval_minutes: number;
  last_scraped_at: string | null;
  last_error: string | null;
  last_run_status: string;
  created_at: string;
}

export interface Job {
  id: number;
  source_id: number | null;
  title: string;
  company: string;
  location: string;
  employment_type: string;
  salary_text: string;
  description_html: string;
  description_text: string;
  skills: string[];
  apply_url: string;
  needs_manual_fill: boolean;
  raw_url: string;
  scraped_at: string;
  last_seen_at?: string | null;
  status: string;
  content_changed: boolean;
}

export interface PaginatedJobs {
  items: Job[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Template {
  id: number;
  channel: string;
  name: string;
  body: string;
  polish_instructions: string;
  is_default: boolean;
}

export interface Draft {
  id: number;
  job_id: number;
  template_id: number;
  channel: string;
  content: string;
  status: string;
  updated_at: string;
}

export interface Revision {
  id: number;
  draft_id: number;
  requirement: string;
  before: string;
  after: string;
  source: string;
  created_at: string;
}

export interface BrandProfile {
  id: number;
  organization_name: string;
  tone: string;
  voice_notes: string;
  banned_words: string;
  hashtag_policy: string;
  cta_preference: string;
}

export interface Settings {
  environment: string;
  ollama_base_url: string | null;
  openai_api_key_configured: boolean;
  anthropic_api_key_configured: boolean;
  gemini_api_key_configured: boolean;
  llm_providers_enabled: boolean;
  api_key_required: boolean;
  scheduler_enabled: boolean;
  archive_missing_jobs: boolean;
}

export interface ScrapeRun {
  id: number;
  source_id: number;
  status: string;
  jobs_found: number;
  jobs_created: number;
  jobs_updated: number;
  jobs_archived: number;
  error_message: string | null;
  duration_ms: number;
  started_at: string;
}

export interface DashboardStats {
  sources_total: number;
  sources_enabled: number;
  jobs_active: number;
  jobs_archived: number;
  jobs_needs_manual_fill: number;
  jobs_changed: number;
  drafts_total: number;
  drafts_reviewed: number;
  scrape_runs_24h: number;
  scrape_failures_24h: number;
  templates_total: number;
  recent_jobs: Job[];
  recent_runs: ScrapeRun[];
}

export interface ScrapeResult {
  source_id: number;
  run_id?: number;
  jobs_found: number;
  jobs_created: number;
  jobs_updated: number;
  jobs_archived: number;
  status: string;
  error_message?: string | null;
  duration_ms: number;
}

export const api = {
  dashboard: () => request<DashboardStats>("/analytics/dashboard"),

  listSources: () => request<Source[]>("/sources"),
  createSource: (data: Partial<Source>) =>
    request<Source>("/sources", { method: "POST", body: JSON.stringify(data) }),
  updateSource: (id: number, data: Partial<Source>) =>
    request<Source>(`/sources/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  scrapeSource: (id: number) =>
    request<ScrapeResult>(`/sources/${id}/scrape`, { method: "POST" }),
  scrapeAll: () =>
    request<{ results: ScrapeResult[]; sources_scraped: number }>("/sources/scrape-all", {
      method: "POST",
    }),
  deleteSource: (id: number) => request<void>(`/sources/${id}`, { method: "DELETE" }),
  listSourceRuns: (id: number) => request<ScrapeRun[]>(`/sources/${id}/runs`),

  listJobs: (params: Record<string, string | number | boolean | undefined> = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "" && v !== null) qs.set(k, String(v));
    });
    const q = qs.toString();
    return request<PaginatedJobs>(`/jobs${q ? `?${q}` : ""}`);
  },
  getJob: (id: number) => request<Job>(`/jobs/${id}`),
  updateJob: (id: number, data: Partial<Job>) =>
    request<Job>(`/jobs/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteJob: (id: number) => request<void>(`/jobs/${id}`, { method: "DELETE" }),

  listTemplates: () => request<Template[]>("/templates"),
  createTemplate: (data: Partial<Template>) =>
    request<Template>("/templates", { method: "POST", body: JSON.stringify(data) }),
  updateTemplate: (id: number, data: Partial<Template>) =>
    request<Template>(`/templates/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteTemplate: (id: number) => request<void>(`/templates/${id}`, { method: "DELETE" }),
  previewTemplate: (id: number, job_id: number, body?: string) =>
    request<{ content: string }>(`/templates/${id}/preview`, {
      method: "POST",
      body: JSON.stringify({ job_id, body }),
    }),

  listDrafts: (jobId?: number) =>
    request<Draft[]>(jobId ? `/drafts?job_id=${jobId}` : "/drafts"),
  generateDrafts: (job_id: number, template_ids: number[]) =>
    request<Draft[]>("/drafts/generate", {
      method: "POST",
      body: JSON.stringify({ job_id, template_ids }),
    }),
  generateBulk: (job_ids: number[], template_ids: number[]) =>
    request<{ drafts: Draft[]; jobs_processed: number }>("/drafts/generate-bulk", {
      method: "POST",
      body: JSON.stringify({ job_ids, template_ids }),
    }),
  updateDraft: (id: number, data: { content?: string; status?: string }) =>
    request<Draft>(`/drafts/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  promptPack: (id: number, requirement = "") =>
    request<{ prompt: string; draft_id: number; channel: string }>(
      `/drafts/${id}/prompt-pack`,
      { method: "POST", body: JSON.stringify({ requirement }) }
    ),
  importResult: (id: number, content: string, requirement = "") =>
    request<Draft>(`/drafts/${id}/import`, {
      method: "POST",
      body: JSON.stringify({ content, requirement }),
    }),
  exportDraft: (id: number, format = "text") =>
    request<{
      content: string;
      channel: string;
      job_title: string;
      company: string;
      markdown?: string | null;
    }>(`/drafts/${id}/export?format=${format}`),
  listRevisions: (id: number) => request<Revision[]>(`/drafts/${id}/revisions`),

  getBrand: () => request<BrandProfile>("/brand"),
  updateBrand: (data: Partial<BrandProfile>) =>
    request<BrandProfile>("/brand", { method: "PATCH", body: JSON.stringify(data) }),

  getSettings: () => request<Settings>("/settings"),
  updateSettings: (data: {
    ollama_base_url?: string | null;
    openai_api_key?: string;
    anthropic_api_key?: string;
    gemini_api_key?: string;
  }) => request<Settings>("/settings", { method: "PATCH", body: JSON.stringify(data) }),
};
