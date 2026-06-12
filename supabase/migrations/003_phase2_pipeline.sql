-- Phase 2: FORGE pipeline tables — extends 001_initial.sql
-- Run after 001_initial.sql and 002_rls_fix.sql

-- ── Extend leads with CSV pipeline fields ─────────────────────────────────────
ALTER TABLE leads ADD COLUMN IF NOT EXISTS owner_confidence text;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS owner_source text;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_confidence text;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS site_tier text;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS reply_status text;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_sent boolean NOT NULL DEFAULT false;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_sent_date timestamptz;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS analysis_notes jsonb;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS is_call_only boolean NOT NULL DEFAULT false;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS approved_flag text DEFAULT 'true';
ALTER TABLE leads ADD COLUMN IF NOT EXISTS dedup_key text;

-- Dedup key for scraper upserts: "name|city|state" lowercase
CREATE UNIQUE INDEX IF NOT EXISTS leads_dedup_key_idx
  ON leads (dedup_key) WHERE dedup_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS leads_email_sent_idx ON leads(email_sent);
CREATE INDEX IF NOT EXISTS leads_is_call_only_idx ON leads(is_call_only);
CREATE INDEX IF NOT EXISTS leads_demo_url_idx ON leads(demo_url) WHERE demo_url IS NOT NULL;

-- ── Website analysis (optional 1:1 extension) ─────────────────────────────────
CREATE TABLE IF NOT EXISTS website_analyses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  has_website boolean,
  mobile_score int,
  speed_score int,
  design_score int,
  seo_score int,
  ai_opportunity_score int,
  signals jsonb NOT NULL DEFAULT '[]',
  raw_notes jsonb,
  analyzed_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (lead_id)
);

-- ── Lead scores (scoring brain output) ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lead_scores (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  website_score int,
  ai_opportunity_score int,
  business_value_score int,
  total_score int NOT NULL,
  tier text NOT NULL,
  reasoning text,
  rubric jsonb,
  scored_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (lead_id)
);

-- ── Pipeline jobs (replaces in-memory _jobs) ─────────────────────────────────
CREATE TABLE IF NOT EXISTS pipeline_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_type text NOT NULL,
  status text NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'running', 'complete', 'failed', 'dead')),
  payload jsonb NOT NULL DEFAULT '{}',
  result jsonb,
  attempts int NOT NULL DEFAULT 0,
  max_attempts int NOT NULL DEFAULT 3,
  error text,
  created_at timestamptz NOT NULL DEFAULT now(),
  started_at timestamptz,
  completed_at timestamptz
);

CREATE INDEX IF NOT EXISTS pipeline_jobs_status_idx ON pipeline_jobs(status);
CREATE INDEX IF NOT EXISTS pipeline_jobs_type_idx ON pipeline_jobs(job_type);

-- ── Email send counters (replaces warmup_state.json + send_log.json) ──────────
CREATE TABLE IF NOT EXISTS email_send_counters (
  id text PRIMARY KEY DEFAULT 'default',
  counter_date date NOT NULL,
  send_count int NOT NULL DEFAULT 0,
  hourly_counts jsonb NOT NULL DEFAULT '{}',
  warmup_start_date date,
  warmup_day int NOT NULL DEFAULT 1,
  daily_limit int,
  last_send_at timestamptz,
  sends jsonb NOT NULL DEFAULT '[]',
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- ── RLS: engine tables are service-role only (no user policies) ─────────────
ALTER TABLE website_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_send_counters ENABLE ROW LEVEL SECURITY;

-- No permissive policies — access via service role key only