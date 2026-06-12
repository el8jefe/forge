/**
 * CRM — Supabase-backed lead store (browser client + RLS)
 * Used from client components; session must be active for reads/writes.
 */

import { getBrowserClient, supabase } from "@/lib/supabase";
import type {
  LeadRecord,
  NormalizedBusiness,
  GeneratedContent,
  ScoreResult,
  LeadQuality,
  LeadStatus,
} from "@/lib/types";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function db() {
  return getBrowserClient();
}

async function requireUserId(): Promise<string> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.user?.id) {
    throw new Error("Sign in required");
  }
  return session.user.id;
}

function rowToRecord(row: Record<string, unknown>): LeadRecord {
  return {
    id: row.id as string,
    business: (row.normalized_data ?? row.business ?? {}) as NormalizedBusiness,
    content: row.content as GeneratedContent | undefined,
    score: row.score_breakdown as ScoreResult | undefined,
    lead_quality: row.lead_quality as LeadQuality | undefined,
    status: (row.status as LeadStatus) ?? "not_contacted",
    notes: row.notes as string | undefined,
    demo_url: row.demo_url as string | undefined,
    created_at: row.created_at as string,
    updated_at: row.updated_at as string,
    contacted_at: row.contacted_at as string | undefined,
  };
}

// ─── Public API ───────────────────────────────────────────────────────────────

export async function getLeads(): Promise<LeadRecord[]> {
  const { data, error } = await db()
    .from("leads")
    .select("*")
    .order("created_at", { ascending: false });
  if (error) throw error;
  return (data ?? []).map(rowToRecord);
}

export async function getLead(id: string): Promise<LeadRecord | null> {
  const { data, error } = await db()
    .from("leads")
    .select("*")
    .eq("id", id)
    .single();
  if (error) return null;
  return data ? rowToRecord(data) : null;
}

export async function addLead(
  business: NormalizedBusiness,
  content?: GeneratedContent,
  score?: ScoreResult,
  lead_quality?: LeadQuality,
  demo_url?: string
): Promise<LeadRecord> {
  const userId = await requireUserId();
  const { data, error } = await db()
    .from("leads")
    .insert({
      user_id: userId,
      business_name: business.name,
      city: business.city,
      state: business.state,
      phone: business.phone ?? null,
      email: business.email ?? null,
      address: business.address ?? null,
      website_url: business.website ?? null,
      business_type: business.service_type,
      google_rating: business.rating ?? null,
      review_count: business.review_count ?? null,
      normalized_data: business,
      content: content ?? null,
      score_breakdown: score ?? null,
      lead_quality: lead_quality ?? null,
      lead_score: score?.score != null ? Math.round(score.score) : null,
      lead_tier: lead_quality?.temperature_short ?? null,
      demo_url: demo_url ?? null,
      status: "not_contacted",
      source: "tradebuilt",
    })
    .select()
    .single();
  if (error) throw error;
  return rowToRecord(data);
}

export async function updateLeadStatus(
  id: string,
  status: LeadStatus,
  notes?: string
): Promise<void> {
  const updates: Record<string, unknown> = { status };
  if (status === "emailed" || status === "called") {
    updates.contacted_at = new Date().toISOString();
  }
  if (notes !== undefined) updates.notes = notes;
  const { error } = await db().from("leads").update(updates).eq("id", id);
  if (error) throw error;
}

export async function updateLeadNotes(id: string, notes: string): Promise<void> {
  const { error } = await db().from("leads").update({ notes }).eq("id", id);
  if (error) throw error;
}

export async function deleteLead(id: string): Promise<void> {
  const { error } = await db().from("leads").delete().eq("id", id);
  if (error) throw error;
}

export async function getLeadsByStatus(status: LeadStatus): Promise<LeadRecord[]> {
  const { data, error } = await db()
    .from("leads")
    .select("*")
    .eq("status", status)
    .order("created_at", { ascending: false });
  if (error) throw error;
  return (data ?? []).map(rowToRecord);
}

export async function clearAll(): Promise<void> {
  const { error } = await db().from("leads").delete().neq("id", "");
  if (error) throw error;
}

// ─── Stats ────────────────────────────────────────────────────────────────────

export interface CrmStats {
  total: number;
  not_contacted: number;
  emailed: number;
  called: number;
  responded: number;
  won: number;
  lost: number;
  burning: number;
  hot: number;
  warm: number;
  cold: number;
}

export async function getStats(): Promise<CrmStats> {
  const { data, error } = await db()
    .from("leads")
    .select("status, lead_quality, lead_tier");
  if (error) throw error;
  const rows = data ?? [];

  const count = (fn: (r: Record<string, unknown>) => boolean) =>
    rows.filter(fn).length;

  return {
    total: rows.length,
    not_contacted: count((r) => r.status === "not_contacted" || r.status === "new"),
    emailed: count((r) => r.status === "emailed"),
    called: count((r) => r.status === "called"),
    responded: count((r) => r.status === "responded" || r.status === "replied"),
    won: count((r) => r.status === "won"),
    lost: count((r) => r.status === "lost"),
    burning: count((r) => {
      const lq = r.lead_quality as { temperature_short?: string } | null;
      return lq?.temperature_short === "burning" || r.lead_tier === "burning";
    }),
    hot: count((r) => {
      const lq = r.lead_quality as { temperature_short?: string } | null;
      return lq?.temperature_short === "hot" || r.lead_tier === "HOT";
    }),
    warm: count((r) => {
      const lq = r.lead_quality as { temperature_short?: string } | null;
      return lq?.temperature_short === "warm" || r.lead_tier === "WARM";
    }),
    cold: count((r) => {
      const lq = r.lead_quality as { temperature_short?: string } | null;
      return lq?.temperature_short === "cold" || r.lead_tier === "COLD";
    }),
  };
}