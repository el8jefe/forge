/**
 * POST /api/booking/book
 * Public endpoint — books an appointment from the web widget.
 */

import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { bookAppointment } from "@/services/booking";
import { sendSms } from "@/services/sms";

const Schema = z.object({
  business_id:    z.string().uuid(),
  customer_name:  z.string().min(1).max(100),
  customer_phone: z.string().min(7).max(20),
  service:        z.string().max(100).optional(),
  start_time:     z.string().datetime(),
  is_recurring:   z.boolean().optional().default(false),
  notes:          z.string().max(500).optional(),
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

    const appt = await bookAppointment({ ...parsed.data, source: "web" });

    // Send confirmation SMS
    const start    = new Date(appt.start_time);
    const dateStr  = start.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
    const timeStr  = start.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
    const smsBody  = `Your appointment${appt.service ? ` for ${appt.service}` : ""} is confirmed for ${dateStr} at ${timeStr}. Reply CANCEL ${appt.id.slice(-6).toUpperCase()} to cancel.`;

    await sendSms(parsed.data.customer_phone, smsBody);

    return NextResponse.json({ appointment: appt }, { status: 201, headers: CORS });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Booking failed";
    return NextResponse.json({ error: msg }, { status: 409, headers: CORS });
  }
}
