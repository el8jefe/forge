import { NextRequest, NextResponse } from "next/server";
import { requireAdminSession } from "@/lib/api-guard";
import { forge } from "@/lib/forge-client";

export async function GET(req: NextRequest) {
  try {
    const session = await requireAdminSession(req);
    if (session instanceof NextResponse) return session;

    const { searchParams } = new URL(req.url);
    const result = await forge.getLeads({
      status: searchParams.get("status") ?? undefined,
      business_type: searchParams.get("business_type") ?? undefined,
      state: searchParams.get("state") ?? undefined,
      tier: searchParams.get("tier") ?? undefined,
      limit: searchParams.get("limit") ? Number(searchParams.get("limit")) : undefined,
      offset: searchParams.get("offset") ? Number(searchParams.get("offset")) : undefined,
    });
    return NextResponse.json(result);
  } catch (err) {
    const msg = err instanceof Error ? err.message : "FORGE unavailable";
    return NextResponse.json({ error: msg }, { status: 502 });
  }
}
