// ─── Input ────────────────────────────────────────────────────────────────────
export interface BusinessInput {
  name: string;
  location: string; // "Denver, CO" or "Denver"
  website?: string;
}

// ─── Normalized ───────────────────────────────────────────────────────────────
export interface NormalizedBusiness {
  name: string;
  service_type: string;
  location: string;
  city: string;
  state: string;
  services: string[];
  tone: "professional" | "friendly" | "urgent" | "premium";
  unique_value_props: string[];
  phone?: string;
  years_in_business?: string;
  email?: string;
  address?: string;
  website?: string;
  review_count?: number;
  rating?: number;
  // Pro/AI mode — injected at generation time for the booking widget
  _bookingBusinessId?: string;
  _apiBase?: string;
}

// ─── Generated Content ────────────────────────────────────────────────────────
export interface ServiceItem {
  name: string;
  description: string;
  icon: string;
}

export interface GeneratedContent {
  hero: string;
  subheadline: string;
  services: ServiceItem[];
  cta: string;
  trust_signals: string[];
  about_snippet: string;
}

// ─── Score ────────────────────────────────────────────────────────────────────
export interface ScoreBreakdown {
  clarity: number;
  specificity: number;
  trust: number;
  conversion: number;
}

export interface ScoreResult {
  score: number;
  breakdown: ScoreBreakdown;
  feedback: string;
  improvements: string[];
  // Lead quality layer
  lead_quality?: LeadQuality;
}

// ─── Lead Quality (Dual-Layer Scoring) ────────────────────────────────────────
export type LeadTemperature = "🔥🔥 Burning Hot" | "🔥 Hot" | "🌡️ Warm" | "❄️ Cold";

export interface LeadQuality {
  temperature: LeadTemperature;
  temperature_short: "burning" | "hot" | "warm" | "cold";
  lead_score: number; // 0-100
  signals: {
    has_phone: boolean;
    has_email: boolean;
    has_address: boolean;
    has_website: boolean;
    website_quality: "none" | "poor" | "ok" | "good";
    review_count: number;
    rating: number;
    years_in_business: boolean;
  };
  reason: string; // e.g. "No website, phone only, 47 reviews — easy win"
}

// ─── CRM ──────────────────────────────────────────────────────────────────────
export type LeadStatus = "not_contacted" | "emailed" | "called" | "responded" | "won" | "lost";

export interface LeadRecord {
  id: string;
  business: NormalizedBusiness;
  content?: GeneratedContent;
  score?: ScoreResult;
  lead_quality?: LeadQuality;
  status: LeadStatus;
  notes?: string;
  demo_url?: string;
  created_at: string;   // ISO
  updated_at: string;   // ISO
  contacted_at?: string;
}

// ─── API Response ─────────────────────────────────────────────────────────────
export interface GenerateSiteResponse {
  business: NormalizedBusiness;
  content: GeneratedContent;
  score: ScoreResult;
  cached: boolean;
  mode?: "forge";
  html?: string;
  demo_url?: string;
}

export interface GenerateSiteError {
  error: string;
  code: "RATE_LIMIT" | "INVALID_INPUT" | "FORGE_ERROR" | "SCRAPE_ERROR";
}

// ─── Email ────────────────────────────────────────────────────────────────────
export interface OutreachEmailPayload {
  to_email: string;
  to_name: string;
  business_name: string;
  demo_url?: string;
  service_type: string;
  city: string;
}
