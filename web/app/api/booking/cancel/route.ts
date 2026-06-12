/**
 * POST /api/booking/cancel
 * Cancels an appointment and triggers waitlist notification.
 */

import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { cancelAppointment } from "@/services/booking";

const Schema = z.object({
  appointment_id: z.string().uuid(),
  business_id:    z.string().uuid(),
});

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export async function OPTIONS() {
  return new NextResponse(null, { status: 204, headers: CORS });
}

export async function POST(req: NextRequest) {
  try {
    const body   = await req.json();
    const parsed = Schema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json(
        { error: parsed.error.issues[0]?.message ?? "Invalid input" },
        { status: 400, headers: CORS }
      );
    }

    await cancelAppointment(parsed.data.appointment_id, parsed.data.business_id);
    return NextResponse.json({ success: true }, { headers: CORS });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Cancel failed";
    return NextResponse.json({ error: msg }, { status: 500, headers: CORS });
  }
}
