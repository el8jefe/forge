/**
 * GET /api/booking/slots?business_id=xxx&days=7
 * Public endpoint — returns available time slots for the next N days.
 * Called by the booking widget embedded in Pro template sites.
 */

import { NextRequest, NextResponse } from "next/server";
import { getUpcomingSlots } from "@/services/booking";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const businessId = searchParams.get("business_id");
  const days       = Math.min(parseInt(searchParams.get("days") ?? "7", 10), 30);

  if (!businessId) {
    return NextResponse.json({ error: "business_id required" }, { status: 400 });
  }

  try {
    const slots = await getUpcomingSlots(businessId, days);
    return NextResponse.json({ slots }, {
      headers: {
        "Access-Control-Allow-Origin": "*", // widget loads from different domain
        "Cache-Control": "no-store",
      },
    });
  } catch (err) {
    console.error("[booking/slots] Error:", err);
    return NextResponse.json({ error: "Failed to load slots" }, { status: 500 });
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, OPTIONS" },
  });
}
