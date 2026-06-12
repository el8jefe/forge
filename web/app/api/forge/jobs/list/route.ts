import { NextRequest, NextResponse } from "next/server";
import { requireAdminSession } from "@/lib/api-guard";
import { forge } from "@/lib/forge-client";

export async function GET(req: NextRequest) {
  try {
    const session = await requireAdminSession(req);
    if (session instanceof NextResponse) return session;

    const limit = Number(new URL(req.url).searchParams.get("limit") ?? "20");
    const result = await forge.listJobs(limit);
    return NextResponse.json(result);
  } catch (err) {
    const msg = err instanceof Error ? err.message : "FORGE unavailable";
    return NextResponse.json({ error: msg }, { status: 502 });
  }
}