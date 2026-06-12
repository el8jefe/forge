/**
 * Booking AI Agent
 * Uses Claude Haiku to parse inbound SMS intent and generate a natural reply.
 * Handles: booking, cancellation, reschedule, availability check, confirmation.
 */

import Anthropic from "@anthropic-ai/sdk";
import type { TimeSlot } from "@/services/booking";

export type BookingIntent =
  | "book"
  | "cancel"
  | "reschedule"
  | "check_availability"
  | "confirm"
  | "waitlist"
  | "greeting"
  | "unknown";

export interface AgentResult {
  intent: BookingIntent;
  slot_date?: string;    // "YYYY-MM-DD"
  slot_time?: string;    // ISO start time
  service?: string;
  customer_name?: string;
  response: string;      // The SMS reply to send back
  complete: boolean;     // true = booking finalized or dead end, clear session
}

interface AgentContext {
  business_name: string;
  business_phone: string;
  services: string[];
  customer_phone: string;
  incoming_message: string;
  session: Record<string, unknown>;          // in-progress booking state
  available_slots: Record<string, TimeSlot[]>; // next 7 days
}

export async function runBookingAgent(ctx: AgentContext): Promise<AgentResult> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return {
      intent: "unknown",
      response: `Hi! To book an appointment with ${ctx.business_name}, please call us directly.`,
      complete: false,
    };
  }

  const client = new Anthropic({ apiKey });

  const slotSummary = buildSlotSummary(ctx.available_slots);
  const serviceList = ctx.services.length > 0 ? ctx.services.join(", ") : "General service";

  const systemPrompt = `You are the AI booking assistant for ${ctx.business_name}. You handle appointment booking via SMS.

Business info:
- Services offered: ${serviceList}
- Available slots (next 7 days): ${slotSummary}

Current conversation state (in-progress booking context):
${JSON.stringify(ctx.session, null, 2)}

Your job:
1. Parse the customer's SMS to understand their intent.
2. If they want to book: collect name, preferred date/time, and service (if applicable).
3. Confirm details before finalizing.
4. If they want to cancel: acknowledge and process.
5. Always be warm, brief, and professional — this is SMS, keep replies under 160 chars when possible.
6. Never make up slot times. Only offer slots from the available list above.
7. If no slots match what they want, offer the nearest available or suggest the waitlist.

Return ONLY valid JSON — no markdown, no extra text:
{
  "intent": "book" | "cancel" | "reschedule" | "check_availability" | "confirm" | "waitlist" | "greeting" | "unknown",
  "slot_date": "YYYY-MM-DD or null",
  "slot_time": "ISO datetime string from available slots, or null",
  "service": "service name or null",
  "customer_name": "extracted name or null",
  "response": "The exact SMS reply to send back to the customer",
  "complete": true | false
}

Rules:
- complete = true when booking is confirmed, cancelled, or conversation is dead-ended
- complete = false when you need more info from the customer
- Never repeat the same question twice
- If the customer says STOP or CANCEL ALL, complete = true with an opt-out response`;

  const userMessage = `Customer phone: ${ctx.customer_phone}
Customer message: "${ctx.incoming_message}"`;

  try {
    const response = await client.messages.create({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 500,
      system: systemPrompt,
      messages: [{ role: "user", content: userMessage }],
    });

    const textBlock = response.content.find((b) => b.type === "text");
    if (!textBlock || textBlock.type !== "text") throw new Error("No text in response");

    const raw = textBlock.text
      .replace(/^```(?:json)?\s*/m, "")
      .replace(/```\s*$/m, "")
      .trim();

    const result = JSON.parse(raw) as AgentResult;
    return result;
  } catch (err) {
    console.error("[booking-agent] Error:", err);
    return {
      intent: "unknown",
      response: `Hi! I had trouble understanding that. Text "BOOK" to schedule an appointment with ${ctx.business_name}, or call us directly.`,
      complete: false,
    };
  }
}

function buildSlotSummary(slots: Record<string, TimeSlot[]>): string {
  if (Object.keys(slots).length === 0) return "No slots available in the next 7 days.";

  return Object.entries(slots)
    .map(([date, daySlots]) => {
      const available = daySlots.filter((s) => s.available);
      if (available.length === 0) return null;
      const labels = available.slice(0, 4).map((s) => `${s.label} (${s.start})`).join(", ");
      return `${date}: ${labels}${available.length > 4 ? ` +${available.length - 4} more` : ""}`;
    })
    .filter(Boolean)
    .join("\n");
}
