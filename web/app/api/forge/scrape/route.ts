import { NextRequest, NextResponse } from "next/server";
import { requireAdminSession } from "@/lib/api-guard";
import { forge } from "@/lib/forge-client";

export async function POST(req: NextRequest) {
  try {
    const session = await requireAdminSession(req);
    if (session instanceof NextResponse) return session;

    const body = await req.json().catch(() => ({}));
    const result = await forge.startScrape(body);
    return NextResponse.json(result);
  } catch (err) {
    const msg = err instanceof Error ? err.message : "FORGE unavailable";
    return NextResponse.json({ error: msg }, { status: 502 });
  }
}
