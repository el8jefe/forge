/**
 * POST /api/send-email
 * Sends outreach email to a business lead.
 */

import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { requireUserSession } from "@/lib/api-guard";
import { sendOutreachEmail } from "@/services/emailer";

const Schema = z.object({
  to_email: z.string().email("Invalid email address"),
  to_name: z.string().min(1).max(100),
  business_name: z.string().min(1).max(120),
  demo_url: z.string().url("Invalid demo URL").optional(),
  service_type: z.string().min(1).max(80),
  city: z.string().min(1).max(80),
});

export async function POST(req: NextRequest) {
  try {
    const session = await requireUserSession(req);
    if (session instanceof NextResponse) return session;

    const body = await req.json();
    const parsed = Schema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { error: parsed.error.issues[0]?.message ?? "Invalid input" },
        { status: 400 }
      );
    }

    const result = await sendOutreachEmail(parsed.data);

    if (!result.success) {
      return NextResponse.json(
        { error: result.error ?? "Failed to send email" },
        { status: 502 }
      );
    }

    return NextResponse.json({ success: true });
  } catch {
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
