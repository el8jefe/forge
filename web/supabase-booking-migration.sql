-- ─── Booking System Migration ──────────────────────────────────────────────────
-- Run this in Supabase SQL Editor after the main migration.

-- Business hours + settings per lead
CREATE TABLE IF NOT EXISTS public.business_hours (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id  uuid REFERENCES public.leads(id) ON DELETE CASCADE,
  twilio_phone text UNIQUE,                        -- the Twilio number assigned to this biz
  slot_duration_mins int NOT NULL DEFAULT 60,      -- how long each appointment slot is
  buffer_mins  int  NOT NULL DEFAULT 0,            -- gap between slots
  -- hours: { "mon": {"open":"09:00","close":"17:00"}, "tue": {...}, ... }
  -- use null for closed days, e.g. "sun": null
  hours        jsonb NOT NULL DEFAULT $${"mon":{"open":"08:00","close":"18:00"},"tue":{"open":"08:00","close":"18:00"},"wed":{"open":"08:00","close":"18:00"},"thu":{"open":"08:00","close":"18:00"},"fri":{"open":"08:00","close":"18:00"},"sat":{"open":"09:00","close":"14:00"},"sun":null}$$,
  services     jsonb NOT NULL DEFAULT '[]',        -- ["AC Repair", "Installation"]
  timezone     text NOT NULL DEFAULT 'America/Denver',
  created_at   timestamptz DEFAULT now(),
  updated_at   timestamptz DEFAULT now()
);

-- Appointments
CREATE TABLE IF NOT EXISTS public.appointments (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id      uuid REFERENCES public.leads(id) ON DELETE CASCADE,
  customer_name    text NOT NULL,
  customer_phone   text NOT NULL,
  service          text,
  start_time       timestamptz NOT NULL,
  end_time         timestamptz NOT NULL,
  status           text NOT NULL DEFAULT 'confirmed'
                     CHECK (status IN ('confirmed','cancelled','completed','no_show')),
  notes            text,
  is_recurring     boolean NOT NULL DEFAULT false,
  recurrence_day   int,                            -- 0=Sun 1=Mon … 6=Sat
  source           text DEFAULT 'web'              -- 'web' | 'sms'
                     CHECK (source IN ('web','sms')),
  cancelled_at     timestamptz,
  created_at       timestamptz DEFAULT now(),
  updated_at       timestamptz DEFAULT now()
);

-- Waitlist — people who want a slot if one opens up
CREATE TABLE IF NOT EXISTS public.waitlist (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id      uuid REFERENCES public.leads(id) ON DELETE CASCADE,
  customer_name    text NOT NULL,
  customer_phone   text NOT NULL,
  requested_date   date,
  service          text,
  notified         boolean NOT NULL DEFAULT false,
  notified_at      timestamptz,
  created_at       timestamptz DEFAULT now()
);

-- SMS session state — keeps track of multi-turn SMS conversations
CREATE TABLE IF NOT EXISTS public.sms_sessions (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_phone   text NOT NULL,
  business_phone   text NOT NULL,
  -- state holds in-progress booking context: { intent, date, time, service, name }
  state            jsonb NOT NULL DEFAULT '{}',
  last_message_at  timestamptz DEFAULT now(),
  UNIQUE (customer_phone, business_phone)
);

-- ─── Indexes ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS appointments_business_id_idx  ON public.appointments(business_id);
CREATE INDEX IF NOT EXISTS appointments_start_time_idx   ON public.appointments(start_time);
CREATE INDEX IF NOT EXISTS appointments_customer_phone   ON public.appointments(customer_phone);
CREATE INDEX IF NOT EXISTS waitlist_business_id_idx      ON public.waitlist(business_id);
CREATE INDEX IF NOT EXISTS sms_sessions_lookup           ON public.sms_sessions(customer_phone, business_phone);

-- ─── RLS ──────────────────────────────────────────────────────────────────────
ALTER TABLE public.business_hours  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.appointments    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.waitlist        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sms_sessions    ENABLE ROW LEVEL SECURITY;

-- Service role has full access (used by our API routes)
DROP POLICY IF EXISTS "service_role_business_hours"  ON public.business_hours;
DROP POLICY IF EXISTS "service_role_appointments"    ON public.appointments;
DROP POLICY IF EXISTS "service_role_waitlist"        ON public.waitlist;
DROP POLICY IF EXISTS "service_role_sms_sessions"    ON public.sms_sessions;

CREATE POLICY "service_role_business_hours" ON public.business_hours
  USING (true) WITH CHECK (true);
CREATE POLICY "service_role_appointments"   ON public.appointments
  USING (true) WITH CHECK (true);
CREATE POLICY "service_role_waitlist"       ON public.waitlist
  USING (true) WITH CHECK (true);
CREATE POLICY "service_role_sms_sessions"   ON public.sms_sessions
  USING (true) WITH CHECK (true);
