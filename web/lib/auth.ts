"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

/**
 * Client-side auth guard.
 * Returns true while checking session — render nothing until it resolves.
 * Redirects to /auth/login if no session found.
 *
 * Usage:
 *   const checking = useAuthGuard();
 *   if (checking) return null;
 */
export function useAuthGuard(): boolean {
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) {
        router.replace("/auth/login");
      } else {
        setChecking(false);
      }
    });
  }, [router]);

  return checking;
}

/**
 * Returns the current session access token, or null.
 * Use when making authenticated API calls (e.g. Stripe checkout).
 */
export async function getAccessToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}
