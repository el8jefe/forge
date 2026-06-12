import { createClient, SupabaseClient } from "@supabase/supabase-js";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _client: SupabaseClient<any> | null = null;

// Browser client — lazy singleton (use for client-side CRM with RLS)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function getBrowserClient(): SupabaseClient<any> {
  if (_client) return _client;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) {
    throw new Error(
      "Supabase not configured. Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to .env.local"
    );
  }
  _client = createClient(url, key);
  return _client;
}

// Named export for auth pages
export const supabase = {
  auth: {
    signInWithPassword: (opts: Parameters<ReturnType<typeof createClient>["auth"]["signInWithPassword"]>[0]) =>
      getBrowserClient().auth.signInWithPassword(opts),
    signUp: (opts: Parameters<ReturnType<typeof createClient>["auth"]["signUp"]>[0]) =>
      getBrowserClient().auth.signUp(opts),
    signOut: () => getBrowserClient().auth.signOut(),
    getSession: () => getBrowserClient().auth.getSession(),
  },
};

// Server client — creates a new instance per call (no singleton, safe in API routes)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function createServerClient(): SupabaseClient<any> {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) throw new Error("Supabase env vars not set");
  return createClient(url, key, { auth: { persistSession: false } });
}
