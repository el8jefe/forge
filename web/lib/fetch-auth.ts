/**
 * fetch-auth.ts — attach Supabase session token to client-side API requests.
 */

import { getAccessToken } from "@/lib/auth";

export async function authFetch(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<Response> {
  const token = await getAccessToken();
  const headers = new Headers(init?.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return fetch(input, { ...init, headers });
}