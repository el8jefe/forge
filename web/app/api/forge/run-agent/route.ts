import { NextRequest, NextResponse } from "next/server";
import { requireUserSession } from "@/lib/api-guard";
import { forge } from "@/lib/forge-client";

export async function POST(req: NextRequest) {
  try {
    const session = await requireUserSession(req);
    if (session instanceof NextResponse) return session;

    const body = await req.json().catch(() => ({}));
    const result = await forge.runAgent(body);
    return NextResponse.json(result);
  } catch (err) {
    const msg = err instanceof Error ? err.message : "FORGE unavailable";
    return NextResponse.json({ error: msg }, { status: 502 });
  }
}