/**
 * api-guard.ts — Phase 0 route protection for TradeBuilt API routes.
 * Validates Supabase session from Authorization: Bearer <access_token>.
 * Set FORGE_ROUTE_AUTH_ENABLED=false to bypass during local debugging only.
 */

import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@/lib/supabase";

export function isRouteAuthEnabled(): boolean {
  return process.env.FORGE_ROUTE_AUTH_ENABLED !== "false";
}

export async function requireUserSession(
  req: NextRequest
): Promise<{ userId: string; email: string | undefined } | NextResponse> {
  if (!isRouteAuthEnabled()) {
    return { userId: "dev-bypass", email: undefined };
  }

  const authHeader = req.headers.get("authorization");
  const token = authHeader?.replace(/^Bearer\s+/i, "").trim();
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const supabase = createServerClient();
    const { data: { user }, error } = await supabase.auth.getUser(token);
    if (error || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    return { userId: user.id, email: user.email };
  } catch {
    return NextResponse.json({ error: "Auth service unavailable" }, { status: 503 });
  }
}