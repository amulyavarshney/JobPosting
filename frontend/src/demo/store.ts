/** In-browser demo store for GitHub Pages (no FastAPI). */

import type {
  BrandProfile,
  DashboardStats,
  Draft,
  DraftQueueItem,
  Job,
  PaginatedJobs,
  Revision,
  ScrapeRun,
  ScrapeResult,
  Settings,
  Source,
  Template,
} from "../api";

const KEY = "jobposting_demo_v1";

type Store = {
  sources: Source[];
  jobs: Job[];
  templates: Template[];
  drafts: Draft[];
  revisions: Revision[];
  brand: BrandProfile;
  runs: ScrapeRun[];
  nextId: number;
};

function now() {
  return new Date().toISOString();
}

function id(store: Store) {
  store.nextId += 1;
  return store.nextId;
}

function seed(): Store {
  const t = now();
  return {
    nextId: 10,
    sources: [
      {
        id: 1,
        name: "Demo Greenhouse",
        kind: "greenhouse",
        base_url: "https://boards.greenhouse.io/demo",
        enabled: true,
        scrape_interval_minutes: 0,
        last_scraped_at: t,
        last_error: null,
        last_run_status: "success",
        created_at: t,
      },
    ],
    jobs: [
      {
        id: 1,
        source_id: 1,
        title: "Senior Backend Engineer",
        company: "Northwind Labs",
        location: "Remote",
        employment_type: "Full-time",
        salary_text: "$160k–$190k",
        description_html: "",
        description_text:
          "Build reliable APIs and data pipelines. Collaborate with product and design. Python/FastAPI experience preferred.",
        skills: ["Python", "FastAPI", "Postgres", "AWS"],
        apply_url: "https://example.com/jobs/backend",
        needs_manual_fill: false,
        raw_url: "https://example.com/jobs/backend",
        scraped_at: t,
        last_seen_at: t,
        status: "active",
        content_changed: false,
      },
      {
        id: 2,
        source_id: 1,
        title: "Product Designer",
        company: "Northwind Labs",
        location: "Bengaluru / Hybrid",
        employment_type: "Full-time",
        salary_text: "",
        description_html: "",
        description_text:
          "Design end-to-end product experiences. Strong Figma skills and systems thinking.",
        skills: ["Figma", "Design systems", "Prototyping"],
        apply_url: "https://example.com/jobs/designer",
        needs_manual_fill: true,
        raw_url: "https://example.com/jobs/designer",
        scraped_at: t,
        last_seen_at: t,
        status: "active",
        content_changed: true,
      },
    ],
    templates: [
      {
        id: 1,
        channel: "linkedin",
        name: "LinkedIn Post",
        body: "We're hiring: {{ job.title }} at {{ job.company }}!\n\n📍 {{ job.location }}\n\n{{ job.description_text[:400] }}\n\nApply: {{ job.apply_url }}",
        polish_instructions: "Keep professional and under 3000 characters.",
        is_default: true,
      },
      {
        id: 2,
        channel: "whatsapp",
        name: "WhatsApp Community",
        body: "*New opening*\n{{ job.title }} @ {{ job.company }}\n{{ job.location }}\nApply: {{ job.apply_url }}",
        polish_instructions: "Short and scannable. No hashtags.",
        is_default: true,
      },
      {
        id: 3,
        channel: "youtube_shorts",
        name: "YouTube Shorts Script",
        body: 'HOOK: "{{ job.company }} is hiring a {{ job.title }}"\nBODY: {{ job.location }}\nCTA: {{ job.apply_url }}',
        polish_instructions: "30–45s spoken script.",
        is_default: true,
      },
      {
        id: 4,
        channel: "instagram_reel",
        name: "Instagram Reel Script",
        body: "[TEXT] Hiring: {{ job.title }}\nVO: Join {{ job.company }} in {{ job.location }}.\nCTA: {{ job.apply_url }}",
        polish_instructions: "Punchy reel script under 45s.",
        is_default: true,
      },
    ],
    drafts: [],
    revisions: [],
    brand: {
      id: 1,
      organization_name: "Northwind Labs",
      tone: "professional, clear, human",
      voice_notes: "Prefer concrete benefits over buzzwords.",
      banned_words: "ninja, rockstar, guru",
      hashtag_policy: "2-5 hashtags on LinkedIn; none on WhatsApp.",
      cta_preference: "End with apply URL.",
    },
    runs: [
      {
        id: 1,
        source_id: 1,
        source_name: "Demo Greenhouse",
        status: "success",
        jobs_found: 2,
        jobs_created: 2,
        jobs_updated: 0,
        jobs_archived: 0,
        error_message: null,
        duration_ms: 420,
        started_at: t,
      },
    ],
  };
}

function load(): Store {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw) as Store;
  } catch {
    /* ignore */
  }
  const s = seed();
  save(s);
  return s;
}

function save(store: Store) {
  localStorage.setItem(KEY, JSON.stringify(store));
}

function renderTemplate(body: string, job: Job): string {
  let out = body;
  const map: Record<string, string> = {
    "job.title": job.title,
    "job.company": job.company,
    "job.location": job.location,
    "job.employment_type": job.employment_type,
    "job.salary_text": job.salary_text,
    "job.apply_url": job.apply_url,
    "job.description_text": job.description_text,
  };
  for (const [k, v] of Object.entries(map)) {
    const token = `{{ ${k} }}`;
    out = out.split(token).join(v || "");
  }
  // crude slice filters e.g. {{ job.description_text[:400] }}
  out = out.replace(
    /\{\{\s*job\.description_text\[:(\d+)\]\s*\}\}/g,
    (_, n) => (job.description_text || "").slice(0, Number(n))
  );
  return out.trim();
}

export const demoApi = {
  dashboard: async (): Promise<DashboardStats> => {
    const s = load();
    const pending: DraftQueueItem[] = s.drafts
      .filter((d) => d.status === "draft")
      .slice(0, 10)
      .map((d) => {
        const job = s.jobs.find((j) => j.id === d.job_id);
        return {
          id: d.id,
          job_id: d.job_id,
          channel: d.channel,
          status: d.status,
          job_title: job?.title || "",
          company: job?.company || "",
          updated_at: d.updated_at,
        };
      });
    return {
      sources_total: s.sources.length,
      sources_enabled: s.sources.filter((x) => x.enabled).length,
      jobs_active: s.jobs.filter((j) => j.status === "active").length,
      jobs_archived: s.jobs.filter((j) => j.status === "archived").length,
      jobs_needs_manual_fill: s.jobs.filter((j) => j.needs_manual_fill && j.status === "active")
        .length,
      jobs_changed: s.jobs.filter((j) => j.content_changed && j.status === "active").length,
      drafts_total: s.drafts.length,
      drafts_reviewed: s.drafts.filter((d) => ["reviewed", "approved"].includes(d.status)).length,
      drafts_pending: s.drafts.filter((d) => d.status === "draft").length,
      scrape_runs_24h: s.runs.length,
      scrape_failures_24h: s.runs.filter((r) => r.status === "failed").length,
      templates_total: s.templates.length,
      recent_jobs: [...s.jobs].sort((a, b) => b.scraped_at.localeCompare(a.scraped_at)).slice(0, 8),
      recent_runs: [...s.runs].slice(0, 8),
      pending_drafts: pending,
    };
  },

  listSources: async () => load().sources,
  createSource: async (data: Partial<Source>) => {
    const s = load();
    const source: Source = {
      id: id(s),
      name: data.name || "Source",
      kind: data.kind || "custom",
      base_url: data.base_url || "",
      enabled: data.enabled ?? true,
      scrape_interval_minutes: data.scrape_interval_minutes ?? 0,
      last_scraped_at: null,
      last_error: null,
      last_run_status: "never",
      created_at: now(),
    };
    s.sources.unshift(source);
    save(s);
    return source;
  },
  updateSource: async (sourceId: number, data: Partial<Source>) => {
    const s = load();
    const source = s.sources.find((x) => x.id === sourceId);
    if (!source) throw new Error("Source not found");
    Object.assign(source, data);
    save(s);
    return source;
  },
  scrapeSource: async (sourceId: number): Promise<ScrapeResult> => {
    const s = load();
    const source = s.sources.find((x) => x.id === sourceId);
    if (!source) throw new Error("Source not found");
    if (!source.enabled) throw new Error("Source is disabled");
    const run: ScrapeRun = {
      id: id(s),
      source_id: sourceId,
      source_name: source.name,
      status: "success",
      jobs_found: s.jobs.filter((j) => j.source_id === sourceId).length,
      jobs_created: 0,
      jobs_updated: 0,
      jobs_archived: 0,
      error_message: null,
      duration_ms: 120,
      started_at: now(),
    };
    s.runs.unshift(run);
    source.last_scraped_at = now();
    source.last_run_status = "success";
    source.last_error = null;
    save(s);
    return {
      source_id: sourceId,
      run_id: run.id,
      jobs_found: run.jobs_found,
      jobs_created: 0,
      jobs_updated: 0,
      jobs_archived: 0,
      status: "success",
      duration_ms: 120,
    };
  },
  scrapeAll: async () => {
    const s = load();
    const results: ScrapeResult[] = [];
    for (const source of s.sources.filter((x) => x.enabled)) {
      results.push(await demoApi.scrapeSource(source.id));
    }
    return { results, sources_scraped: results.length };
  },
  deleteSource: async (sourceId: number) => {
    const s = load();
    s.sources = s.sources.filter((x) => x.id !== sourceId);
    s.jobs = s.jobs.filter((j) => j.source_id !== sourceId);
    save(s);
  },
  listSourceRuns: async (sourceId: number) => load().runs.filter((r) => r.source_id === sourceId),

  listJobs: async (
    params: Record<string, string | number | boolean | undefined> = {}
  ): Promise<PaginatedJobs> => {
    const s = load();
    let items = [...s.jobs];
    const status = String(params.status ?? "active");
    if (status && status !== "all") items = items.filter((j) => j.status === status);
    if (params.q) {
      const q = String(params.q).toLowerCase();
      items = items.filter(
        (j) =>
          j.title.toLowerCase().includes(q) ||
          j.company.toLowerCase().includes(q) ||
          j.location.toLowerCase().includes(q)
      );
    }
    if (params.source_id !== undefined)
      items = items.filter((j) => j.source_id === Number(params.source_id));
    if (params.needs_manual_fill !== undefined)
      items = items.filter((j) => j.needs_manual_fill === Boolean(params.needs_manual_fill));
    if (params.content_changed !== undefined)
      items = items.filter((j) => j.content_changed === Boolean(params.content_changed));
    items.sort((a, b) => b.scraped_at.localeCompare(a.scraped_at));
    const page = Number(params.page || 1);
    const page_size = Number(params.page_size || 50);
    const total = items.length;
    const pages = Math.max(1, Math.ceil(total / page_size));
    const start = (page - 1) * page_size;
    return { items: items.slice(start, start + page_size), total, page, page_size, pages };
  },
  getJob: async (jobId: number) => {
    const job = load().jobs.find((j) => j.id === jobId);
    if (!job) throw new Error("Job not found");
    return job;
  },
  updateJob: async (jobId: number, data: Partial<Job>) => {
    const s = load();
    const job = s.jobs.find((j) => j.id === jobId);
    if (!job) throw new Error("Job not found");
    Object.assign(job, data);
    save(s);
    return job;
  },
  deleteJob: async (jobId: number) => {
    const s = load();
    s.jobs = s.jobs.filter((j) => j.id !== jobId);
    s.drafts = s.drafts.filter((d) => d.job_id !== jobId);
    save(s);
  },

  listTemplates: async () => load().templates,
  createTemplate: async (data: Partial<Template>) => {
    const s = load();
    const tpl: Template = {
      id: id(s),
      channel: data.channel || "custom",
      name: data.name || "Template",
      body: data.body || "{{ job.title }}",
      polish_instructions: data.polish_instructions || "",
      is_default: Boolean(data.is_default),
    };
    s.templates.push(tpl);
    save(s);
    return tpl;
  },
  updateTemplate: async (templateId: number, data: Partial<Template>) => {
    const s = load();
    const tpl = s.templates.find((t) => t.id === templateId);
    if (!tpl) throw new Error("Template not found");
    Object.assign(tpl, data);
    save(s);
    return tpl;
  },
  deleteTemplate: async (templateId: number) => {
    const s = load();
    s.templates = s.templates.filter((t) => t.id !== templateId);
    save(s);
  },
  previewTemplate: async (templateId: number, jobId: number, body?: string) => {
    const s = load();
    const tpl = s.templates.find((t) => t.id === templateId);
    const job = s.jobs.find((j) => j.id === jobId);
    if (!tpl || !job) throw new Error("Template or job not found");
    return { content: renderTemplate(body ?? tpl.body, job) };
  },

  listDrafts: async (jobId?: number, status?: string) => {
    let drafts = load().drafts;
    if (jobId !== undefined) drafts = drafts.filter((d) => d.job_id === jobId);
    if (status) drafts = drafts.filter((d) => d.status === status);
    return drafts.sort((a, b) => b.updated_at.localeCompare(a.updated_at));
  },
  generateDrafts: async (jobId: number, templateIds: number[], overwrite = false) => {
    const s = load();
    const job = s.jobs.find((j) => j.id === jobId);
    if (!job) throw new Error("Job not found");
    const results: Draft[] = [];
    for (const tid of templateIds) {
      const tpl = s.templates.find((t) => t.id === tid);
      if (!tpl) continue;
      const content = renderTemplate(tpl.body, job);
      let existing = s.drafts.find((d) => d.job_id === jobId && d.template_id === tid);
      if (existing) {
        if (["reviewed", "approved", "exported"].includes(existing.status) && !overwrite) {
          results.push(existing);
          continue;
        }
        existing.content = content;
        existing.status = "draft";
        existing.channel = tpl.channel;
        existing.updated_at = now();
        results.push(existing);
      } else {
        existing = {
          id: id(s),
          job_id: jobId,
          template_id: tid,
          channel: tpl.channel,
          content,
          status: "draft",
          updated_at: now(),
        };
        s.drafts.push(existing);
        results.push(existing);
      }
    }
    save(s);
    return results;
  },
  generateBulk: async (jobIds: number[], templateIds: number[], overwrite = false) => {
    const drafts: Draft[] = [];
    for (const jid of jobIds) {
      drafts.push(...(await demoApi.generateDrafts(jid, templateIds, overwrite)));
    }
    return { drafts, jobs_processed: jobIds.length };
  },
  updateDraft: async (draftId: number, data: { content?: string; status?: string }) => {
    const s = load();
    const draft = s.drafts.find((d) => d.id === draftId);
    if (!draft) throw new Error("Draft not found");
    if (data.content !== undefined && data.content !== draft.content) {
      s.revisions.unshift({
        id: id(s),
        draft_id: draftId,
        requirement: "Manual edit",
        before: draft.content,
        after: data.content,
        source: "manual",
        created_at: now(),
      });
      draft.content = data.content;
    }
    if (data.status !== undefined) draft.status = data.status;
    draft.updated_at = now();
    save(s);
    return draft;
  },
  promptPack: async (draftId: number, requirement = "") => {
    const s = load();
    const draft = s.drafts.find((d) => d.id === draftId);
    if (!draft) throw new Error("Draft not found");
    const job = s.jobs.find((j) => j.id === draft.job_id);
    const tpl = s.templates.find((t) => t.id === draft.template_id);
    const prompt = [
      "# JobPosting AI Polish Task",
      `## Channel: ${draft.channel}`,
      `## Brand: ${s.brand.organization_name} (${s.brand.tone})`,
      `## Polish instructions`,
      tpl?.polish_instructions || "",
      `## Job`,
      JSON.stringify(job, null, 2),
      `## Current draft`,
      draft.content,
      requirement ? `## Custom requirement\n${requirement}` : "",
      "## Output\nProvide the polished final copy only.",
    ]
      .filter(Boolean)
      .join("\n\n");
    return { prompt, draft_id: draftId, channel: draft.channel };
  },
  importResult: async (draftId: number, content: string, requirement = "") => {
    const s = load();
    const draft = s.drafts.find((d) => d.id === draftId);
    if (!draft) throw new Error("Draft not found");
    s.revisions.unshift({
      id: id(s),
      draft_id: draftId,
      requirement: requirement || "AI import",
      before: draft.content,
      after: content,
      source: "import",
      created_at: now(),
    });
    draft.content = content;
    draft.status = "reviewed";
    draft.updated_at = now();
    save(s);
    return draft;
  },
  exportDraft: async (draftId: number, format = "text") => {
    const s = load();
    const draft = s.drafts.find((d) => d.id === draftId);
    if (!draft) throw new Error("Draft not found");
    const job = s.jobs.find((j) => j.id === draft.job_id);
    const markdown = `# ${job?.title || ""} — ${job?.company || ""}\n\n${draft.content}\n`;
    return {
      content: draft.content,
      channel: draft.channel,
      job_title: job?.title || "",
      company: job?.company || "",
      markdown: format === "markdown" ? markdown : null,
    };
  },
  listRevisions: async (draftId: number) =>
    load().revisions.filter((r) => r.draft_id === draftId),

  getBrand: async () => load().brand,
  updateBrand: async (data: Partial<BrandProfile>) => {
    const s = load();
    Object.assign(s.brand, data);
    save(s);
    return s.brand;
  },
  getSettings: async (): Promise<Settings> => ({
    environment: "demo",
    ollama_base_url: null,
    openai_api_key_configured: false,
    anthropic_api_key_configured: false,
    gemini_api_key_configured: false,
    llm_providers_enabled: false,
    api_key_required: false,
    scheduler_enabled: false,
    archive_missing_jobs: true,
  }),
};

export const isDemoMode = () => import.meta.env.VITE_DEMO_MODE === "true";
