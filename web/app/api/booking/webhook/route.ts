/**
 * POST /api/booking/webhook
 * Twilio inbound SMS webhook.
 * Twilio sends a POST with From, To, Body fields (form-encoded).
 * We parse intent with the AI agent, update booking state, send an SMS reply.
 */

import { NextRequest, NextResponse } from "next/server";
import {
  getAvailableSlots,
  getUpcomingSlots,
  bookAppointment,
  cancelAppointment,
  addToWaitlist,
  getSession,
  saveSession,
  clearSession,
  getBusinessHours,
} from "@/services/booking";
import { runBookingAgent } from "@/services/booking-agent";
import { sendSms } from "@/services/sms";
import { createServerClient } from "@/lib/supabase";

export async function POST(req: NextRequest) {
  try {
    // Twilio sends form-encoded data
    const formData = await req.formData();
    const from         = formData.get("From") as string;  // customer phone
    const to           = formData.get("To")   as string;  // our Twilio number
    const body         = formData.get("Body") as string;  // customer message

    if (!from || !to || !body) {
      return twimlResponse(""); // empty TwiML = no reply (Twilio needs valid XML)
    }

    // Look up which business owns this Twilio number
    const db = createServerClient();
    const { data: hoursRow } = await db
      .from("business_hours")
      .select("*, leads(id, business_name, services)")
      .eq("twilio_phone", to)
      .single();

    if (!hoursRow) {
      await sendSms(from, "Sorry, this number is not configured for bookings.");
      return twimlResponse("");
    }

    const businessId   = hoursRow.business_id as string;
    const businessName = (hoursRow as { leads?: { business_name?: string } }).leads?.business_name ?? "this business";
    const services     = (hoursRow.services as string[]) ?? [];

    // Load conversation session
    const session = await getSession(from, to);

    // Load available slots for AI context
    const availableSlots = await getUpcomingSlots(businessId, 7);

    // Run AI agent
    const result = await runBookingAgent({
      business_name:   businessName,
      business_phone:  to,
      services,
      customer_phone:  from,
      incoming_message: body.trim(),
      session,
      available_slots: availableSlots,
    });

    // Execute the intent
    if (result.intent === "book" && result.slot_time && result.customer_name && result.complete) {
      try {
        const appt = await bookAppointment({
          business_id:    businessId,
          customer_name:  result.customer_name,
          customer_phone: from,
          service:        result.service,
          start_time:     result.slot_time,
          source:         "sms",
        });
        await clearSession(from, to);

        // Format confirmation
        const start = new Date(appt.start_time);
        const dateStr = start.toLocaleDateString("en-US", { weekday: "long", month: "short", day: "numeric" });
        const timeStr = start.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
        const confirmMsg = `Confirmed! ${result.service ? result.service + " " : ""}appt for ${result.customer_name} on ${dateStr} at ${timeStr}. Reply CANCEL ${appt.id.slice(-6).toUpperCase()} to cancel.`;
        await sendSms(from, confirmMsg);
      } catch {
        await sendSms(from, "Sorry, that slot was just taken. " + result.response);
      }
    } else if (result.intent === "waitlist" && result.complete) {
      await addToWaitlist({
        business_id:    businessId,
        customer_name:  result.customer_name ?? from,
        customer_phone: from,
        service:        result.service,
      });
      await clearSession(from, to);
      await sendSms(from, result.response);
    } else if (result.intent === "cancel" && result.complete) {
      // Try to extract appointment ID from message (last 6 chars pattern)
      const idMatch = body.match(/[A-Z0-9]{6}$/i);
      if (idMatch) {
        const { data: appts } = await db
          .from("appointments")
          .select("id")
          .eq("business_id", businessId)
          .eq("customer_phone", from)
          .eq("status", "confirmed")
          .ilike("id", `%${idMatch[0].toLowerCase()}`);

        if (appts && appts.length > 0) {
          await cancelAppointment(appts[0].id, businessId);
        }
      }
      await clearSession(from, to);
      await sendSms(from, result.response);
    } else {
      // Multi-turn — save updated session state and reply
      const newSession = {
        ...session,
        intent:       result.intent,
        slot_date:    result.slot_date  ?? session.slot_date,
        slot_time:    result.slot_time  ?? session.slot_time,
        service:      result.service    ?? session.service,
        customer_name: result.customer_name ?? session.customer_name,
      };

      if (result.complete) {
        await clearSession(from, to);
      } else {
        await saveSession(from, to, newSession);
      }

      await sendSms(from, result.response);
    }

    // Return empty TwiML — we already sent our reply via API
    return twimlResponse("");
  } catch (err) {
    console.error("[booking/webhook] Error:", err);
    return twimlResponse("");
  }
}

function twimlResponse(message: string): NextResponse {
  const xml = message
    ? `<?xml version="1.0" encoding="UTF-8"?><Response><Message>${message}</Message></Response>`
    : `<?xml version="1.0" encoding="UTF-8"?><Response></Response>`;
  return new NextResponse(xml, {
    status: 200,
    headers: { "Content-Type": "text/xml" },
  });
}
