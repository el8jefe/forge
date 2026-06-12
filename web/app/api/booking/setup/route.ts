/**
 * POST /api/booking/setup
 * Creates or updates business hours settings for a lead.
 * Called from the dashboard when a Pro customer sets up their booking.
 */

import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { upsertBusinessHours } from "@/services/booking";

const DaySchema = z.object({ open: z.string(), close: z.string() }).nullable();

const Schema = z.object({
  business_id:        z.string().uuid(),
  twilio_phone:       z.string().optional(),
  slot_duration_mins: z.number().min(15).max(480).optional(),
  buffer_mins:        z.number().min(0).max(120).optional(),
  services:           z.array(z.string()).optional(),
  timezone:           z.string().optional(),
  hours: z.object({
    mon: DaySchema, tue: DaySchema, wed: DaySchema,
    thu: DaySchema, fri: DaySchema, sat: DaySchema, sun: DaySchema,
  }).optional(),
});

export async function POST(req: NextRequest) {
  try {
    const body   = await req.json();
    const parsed = Schema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json(
        { error: parsed.error.issues[0]?.message ?? "Invalid input" },
        { status: 400 }
      );
    }

    const { business_id, ...settings } = parsed.data;
    await upsertBusinessHours(business_id, settings);
    return NextResponse.json({ success: true });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Setup failed";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
