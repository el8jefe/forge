-- ============================================================
-- TRADEBUILT + FORGE Unified Schema
-- Run in: supabase.com dashboard → SQL editor
-- Project: iixtlxrwisdxloviamg
-- ============================================================

-- ── User profiles (extends Supabase Auth) ────────────────────
CREATE TABLE IF NOT EXISTS user_profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  plan text NOT NULL DEFAULT 'free',        -- 'free' | 'pro' | 'agency'
  stripe_customer_id text,
  stripe_subscription_id text,
  generates_used int NOT NULL DEFAULT 0,
  emails_sent_today int NOT NULL DEFAULT 0,
  daily_email_limit int NOT NULL DEFAULT 80,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- ── Leads (unified — covers FORGE CSV + Tradebuilt types) ────
CREATE TABLE IF NOT EXISTS leads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Business identity
  business_name text NOT NULL,
  owner_name text,
  email text,
  phone text,
  city text,
  state text,
  address text,
  business_type text,             -- hvac, plumber, electrician, etc.

  -- Website quality signals (FORGE scoring)
  website_url text,
  website_status text,            -- no_website | poor | ok | good
  google_rating numeric,
  review_count int,

  -- Scoring
  forge_score int,                -- FORGE 0-12 raw score
  lead_score int,                 -- Tradebuilt 0-100 score
  lead_tier text,                 -- HOT | WARM | COLD | burning | hot | warm | cold
  score_breakdown jsonb,          -- { clarity, specificity, trust, conversion }

  -- Generated content (Tradebuilt style)
  content jsonb,                  -- { hero, subheadline, services, cta, ... }
  normalized_data jsonb,          -- full NormalizedBusiness object
  lead_quality jsonb,             -- full LeadQuality object

  -- Demo site
  demo_url text,                  -- live GitHub Pages or hosted URL
  demo_html text,                 -- full HTML snapshot
  site_built_at timestamptz,

  -- CRM status
  status text NOT NULL DEFAULT 'new',
  -- new | site_built | emailed | followed_up | replied | won | lost
  notes text,
  approved boolean DEFAULT true,

  -- Source tracking
  source text NOT NULL DEFAULT 'manual',
  -- manual | forge_scraper | tradebuilt

  -- Timestamps
  date_scraped timestamptz DEFAULT now(),
  contacted_at timestamptz,
  replied_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- ── Outreach log (replaces log.csv + followup_log.csv) ───────
CREATE TABLE IF NOT EXISTS outreach_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,

  type text NOT NULL,             -- initial | followup
  to_email text,
  to_name text,
  subject text,
  demo_url text,

  sent_at timestamptz DEFAULT now(),
  opened_at timestamptz,
  clicked_at timestamptz,
  replied_at timestamptz,
  reply_content text,

  success boolean DEFAULT true,
  error_message text
);

-- ── Scrape jobs (tracks background FORGE runs) ───────────────
CREATE TABLE IF NOT EXISTS scrape_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,

  status text NOT NULL DEFAULT 'pending',
  -- pending | running | complete | failed

  business_types text[],          -- ['hvac', 'plumber', ...]
  states text[],                  -- ['CT', 'NY', ...]
  max_leads int DEFAULT 100,

  leads_found int DEFAULT 0,
  sites_built int DEFAULT 0,
  emails_sent int DEFAULT 0,

  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),

  error text
);

-- ── Clients (paying businesses) ──────────────────────────────
CREATE TABLE IF NOT EXISTS clients (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid REFERENCES leads(id),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,

  business_name text NOT NULL,
  email text NOT NULL,
  phone text,

  plan text NOT NULL DEFAULT 'basic',  -- basic | pro | white_label
  status text NOT NULL DEFAULT 'active', -- active | paused | cancelled

  demo_url text,
  stripe_customer_id text,
  stripe_subscription_id text,
  monthly_amount int,             -- in cents

  magic_code text UNIQUE,         -- client portal login code
  last_login_at timestamptz,

  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- ── Indexes ──────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS leads_user_id_idx      ON leads(user_id);
CREATE INDEX IF NOT EXISTS leads_status_idx        ON leads(status);
CREATE INDEX IF NOT EXISTS leads_source_idx        ON leads(source);
CREATE INDEX IF NOT EXISTS leads_business_type_idx ON leads(business_type);
CREATE INDEX IF NOT EXISTS leads_state_idx         ON leads(state);
CREATE INDEX IF NOT EXISTS outreach_lead_id_idx    ON outreach_log(lead_id);
CREATE INDEX IF NOT EXISTS scrape_jobs_user_idx    ON scrape_jobs(user_id);
CREATE INDEX IF NOT EXISTS clients_user_id_idx     ON clients(user_id);

-- ── Row Level Security ───────────────────────────────────────
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads          ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach_log   ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_jobs    ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients        ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "users see own profile"            ON user_profiles;
DROP POLICY IF EXISTS "users see own leads"              ON leads;
DROP POLICY IF EXISTS "users see own outreach"           ON outreach_log;
DROP POLICY IF EXISTS "users see own jobs"               ON scrape_jobs;
DROP POLICY IF EXISTS "users see own clients"            ON clients;
DROP POLICY IF EXISTS "service role full access leads"   ON leads;
DROP POLICY IF EXISTS "service role full access outreach" ON outreach_log;
DROP POLICY IF EXISTS "service role full access jobs"    ON scrape_jobs;
DROP POLICY IF EXISTS "service role full access clients" ON clients;

CREATE POLICY "users see own profile"   ON user_profiles FOR ALL USING (auth.uid() = id);
CREATE POLICY "users see own leads"     ON leads          FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "users see own outreach"  ON outreach_log   FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "users see own jobs"      ON scrape_jobs    FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "users see own clients"   ON clients        FOR ALL USING (auth.uid() = user_id);

-- NOTE: Do NOT add permissive USING (true) policies here.
-- Supabase service_role key bypasses RLS automatically for backend writes.
-- Permissive policies OR'd with user policies would expose all rows to every user.

-- ── Auto-create profile on signup ────────────────────────────
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.user_profiles (id) VALUES (NEW.id)
    ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
EXCEPTION WHEN OTHERS THEN
  -- Never block signup if profile creation fails
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ── updated_at auto-trigger ───────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS leads_updated_at    ON leads;
DROP TRIGGER IF EXISTS profiles_updated_at ON user_profiles;
DROP TRIGGER IF EXISTS clients_updated_at  ON clients;

CREATE TRIGGER leads_updated_at    BEFORE UPDATE ON leads         FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER clients_updated_at  BEFORE UPDATE ON clients       FOR EACH ROW EXECUTE FUNCTION update_updated_at();
