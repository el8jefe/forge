/**
 * forge-client.ts — typed HTTP client for the FORGE API
 * Used by Tradebuilt API routes to call the FORGE engine.
 */

const FORGE_URL = process.env.FORGE_API_URL ?? "http://localhost:8000";
const FORGE_API_KEY = process.env.FORGE_API_KEY ?? "";

export interface ForgeJob {
  id: string;
  type: string;
  status: "pending" | "running" | "complete" | "failed" | "dead";
  leads_found?: number;
  sites_built?: number;
  emails_sent?: number;
  started_at?: string;
  completed_at?: string;
  error?: string;
  params?: Record<string, unknown>;
  result?: Record<string, unknown>;
}

export interface ForgeLead {
  id: string;
  business_name: string;
  email?: string;
  phone?: string;
  city?: string;
  state?: string;
  business_type?: string;
  website_url?: string;
  forge_score?: number;
  lead_score?: number;
  lead_tier?: string;
  demo_url?: string;
  status: string;
  source: string;
  created_at: string;
}

export interface ForgeBuildSiteResult {
  html: string;
  demo_url?: string | null;
  business_name: string;
  city: string;
  state: string;
  business_type: string;
  lead_tier: string;
  phone?: string;
}

export interface ScrapeOptions {
  business_types?: string[];
  states?: string[];
  max_leads?: number;
}

export interface BuildSiteOptions {
  name: string;
  location: string;
  website?: string;
  business_type?: string;
  deploy?: boolean;
  lead_tier?: string;
}

function forgeHeaders(extra?: HeadersInit): HeadersInit {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (FORGE_API_KEY) headers["X-FORGE-API-Key"] = FORGE_API_KEY;
  return { ...headers, ...(extra as Record<string, string> | undefined) };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${FORGE_URL}${path}`, {
    ...init,
    headers: forgeHeaders(init?.headers),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`FORGE API ${path} → ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const forge = {
  health: () =>
    request<{ status: string; version: string; celery: boolean; storage: string }>("/health"),

  getLeads: (params?: {
    status?: string;
    business_type?: string;
    state?: string;
    tier?: string;
    limit?: number;
    offset?: number;
  }) => {
    const qs = new URLSearchParams(
      Object.entries(params ?? {})
        .filter(([, v]) => v !== undefined)
        .map(([k, v]) => [k, String(v)])
    ).toString();
    return request<{ leads: ForgeLead[]; total: number }>(`/leads${qs ? `?${qs}` : ""}`);
  },

  updateLead: (id: string, body: { status?: string; notes?: string; approved?: boolean }) =>
    request<{ lead: ForgeLead }>(`/leads/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  buildSite: (opts: BuildSiteOptions) =>
    request<ForgeBuildSiteResult>("/build-site", {
      method: "POST",
      body: JSON.stringify(opts),
    }),

  startScrape: (opts: ScrapeOptions = {}) =>
    request<{ job_id: string; status: string }>("/scrape", {
      method: "POST",
      body: JSON.stringify(opts),
    }),

  runAgent: (opts: { lead_ids?: string[]; send_emails?: boolean } = {}) =>
    request<{ job_id: string; status: string }>("/run-agent", {
      method: "POST",
      body: JSON.stringify(opts),
    }),

  runFollowup: () =>
    request<{ job_id: string; status: string }>("/followup", { method: "POST" }),

  runPipeline: () =>
    request<{ job_id: string; status: string }>("/run-pipeline", { method: "POST" }),

  getJob: (jobId: string) => request<ForgeJob>(`/jobs/${jobId}`),

  listJobs: (limit = 20) =>
    request<{ jobs: ForgeJob[] }>(`/jobs?limit=${limit}`),

  getStats: () =>
    request<{ total: number; by_status: Record<string, number>; by_tier: Record<string, number> }>(
      "/stats"
    ),
};