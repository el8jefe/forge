-- Phase 0 security fix — run in Supabase SQL editor if you already applied the old migration.
-- Removes permissive RLS policies that allowed cross-user data access.

DROP POLICY IF EXISTS "service role full access leads"    ON leads;
DROP POLICY IF EXISTS "service role full access outreach" ON outreach_log;
DROP POLICY IF EXISTS "service role full access jobs"     ON scrape_jobs;
DROP POLICY IF EXISTS "service role full access clients"  ON clients;

-- Backend writes use SUPABASE_SERVICE_ROLE_KEY which bypasses RLS — no extra policy needed.