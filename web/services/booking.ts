/**
 * Booking Service
 * Handles availability calculation, appointment CRUD, and waitlist management.
 */

import { createServerClient } from "@/lib/supabase";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface DayHours {
  open: string;  // "09:00"
  close: string; // "17:00"
}

export interface BusinessHours {
  id: string;
  business_id: string;
  twilio_phone: string | null;
  slot_duration_mins: number;
  buffer_mins: number;
  hours: Record<string, DayHours | null>; // "mon" | "tue" | ... → null if closed
  services: string[];
  timezone: string;
}

export interface Appointment {
  id: string;
  business_id: string;
  customer_name: string;
  customer_phone: string;
  service: string | null;
  start_time: string; // ISO
  end_time: string;   // ISO
  status: "confirmed" | "cancelled" | "completed" | "no_show";
  notes: string | null;
  is_recurring: boolean;
  recurrence_day: number | null;
  source: "web" | "sms";
  created_at: string;
}

export interface TimeSlot {
  start: string; // ISO
  end: string;   // ISO
  label: string; // "9:00 AM"
  available: boolean;
}

// ─── Day helpers ──────────────────────────────────────────────────────────────

const DAY_KEYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];

function toMinutes(time: string): number {
  const [h, m] = time.split(":").map(Number);
  return h * 60 + m;
}

function formatTime(date: Date): string {
  const h = date.getHours();
  const m = date.getMinutes();
  const ampm = h >= 12 ? "PM" : "AM";
  const h12 = h % 12 || 12;
  return `${h12}:${m.toString().padStart(2, "0")} ${ampm}`;
}

// ─── Availability ──────────────────────────────────────────────────────────────

/**
 * Returns available slots for a business on a given date (YYYY-MM-DD).
 * Filters out slots that already have confirmed appointments.
 */
export async function getAvailableSlots(
  businessId: string,
  date: string // "YYYY-MM-DD"
): Promise<TimeSlot[]> {
  const db = createServerClient();

  const { data: hoursRow } = await db
    .from("business_hours")
    .select("*")
    .eq("business_id", businessId)
    .single();

  if (!hoursRow) return [];

  const bh = hoursRow as BusinessHours;
  const dayOfWeek = new Date(date + "T12:00:00").getDay(); // use noon to avoid DST edge
  const dayKey = DAY_KEYS[dayOfWeek];
  const dayHours = bh.hours[dayKey];

  if (!dayHours) return []; // closed

  const openMin  = toMinutes(dayHours.open);
  const closeMin = toMinutes(dayHours.close);
  const step     = bh.slot_duration_mins + bh.buffer_mins;

  // Fetch existing confirmed appointments for this date
  const dayStart = `${date}T00:00:00.000Z`;
  const dayEnd   = `${date}T23:59:59.999Z`;

  const { data: existing } = await db
    .from("appointments")
    .select("start_time, end_time")
    .eq("business_id", businessId)
    .eq("status", "confirmed")
    .gte("start_time", dayStart)
    .lte("start_time", dayEnd);

  const bookedStarts = new Set(
    (existing ?? []).map((a: { start_time: string }) =>
      new Date(a.start_time).toISOString()
    )
  );

  const slots: TimeSlot[] = [];

  for (let min = openMin; min + bh.slot_duration_mins <= closeMin; min += step) {
    const [y, mo, d] = date.split("-").map(Number);
    const startDate = new Date(y, mo - 1, d, Math.floor(min / 60), min % 60, 0);
    const endDate   = new Date(startDate.getTime() + bh.slot_duration_mins * 60000);

    // Skip slots in the past
    if (startDate < new Date()) continue;

    const isoStart = startDate.toISOString();
    slots.push({
      start: isoStart,
      end: endDate.toISOString(),
      label: formatTime(startDate),
      available: !bookedStarts.has(isoStart),
    });
  }

  return slots;
}

/**
 * Returns available slots for the next N days (default 7).
 */
export async function getUpcomingSlots(
  businessId: string,
  days = 7
): Promise<Record<string, TimeSlot[]>> {
  const result: Record<string, TimeSlot[]> = {};
  const today = new Date();

  for (let i = 0; i < days; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    const dateStr = d.toISOString().split("T")[0];
    const slots = await getAvailableSlots(businessId, dateStr);
    if (slots.length > 0) result[dateStr] = slots;
  }

  return result;
}

// ─── CRUD ─────────────────────────────────────────────────────────────────────

export async function bookAppointment(params: {
  business_id: string;
  customer_name: string;
  customer_phone: string;
  service?: string;
  start_time: string; // ISO
  source?: "web" | "sms";
  notes?: string;
  is_recurring?: boolean;
}): Promise<Appointment> {
  const db = createServerClient();

  // Fetch slot duration to compute end_time
  const { data: hoursRow } = await db
    .from("business_hours")
    .select("slot_duration_mins")
    .eq("business_id", params.business_id)
    .single();

  const slotMins = (hoursRow as { slot_duration_mins: number } | null)?.slot_duration_mins ?? 60;
  const start = new Date(params.start_time);
  const end   = new Date(start.getTime() + slotMins * 60000);

  // Check slot is still available
  const { data: conflict } = await db
    .from("appointments")
    .select("id")
    .eq("business_id", params.business_id)
    .eq("status", "confirmed")
    .eq("start_time", params.start_time)
    .single();

  if (conflict) throw new Error("That slot is no longer available.");

  const { data, error } = await db
    .from("appointments")
    .insert({
      business_id:    params.business_id,
      customer_name:  params.customer_name,
      customer_phone: params.customer_phone,
      service:        params.service ?? null,
      start_time:     start.toISOString(),
      end_time:       end.toISOString(),
      status:         "confirmed",
      notes:          params.notes ?? null,
      is_recurring:   params.is_recurring ?? false,
      recurrence_day: params.is_recurring ? start.getDay() : null,
      source:         params.source ?? "web",
    })
    .select()
    .single();

  if (error) throw error;
  return data as Appointment;
}

export async function cancelAppointment(
  appointmentId: string,
  businessId: string
): Promise<void> {
  const db = createServerClient();
  const { error } = await db
    .from("appointments")
    .update({ status: "cancelled", cancelled_at: new Date().toISOString() })
    .eq("id", appointmentId)
    .eq("business_id", businessId);
  if (error) throw error;

  // Notify first person on waitlist for this business
  await notifyWaitlist(businessId);
}

export async function getAppointments(
  businessId: string,
  from?: string,
  to?: string
): Promise<Appointment[]> {
  const db = createServerClient();
  let q = db
    .from("appointments")
    .select("*")
    .eq("business_id", businessId)
    .order("start_time", { ascending: true });

  if (from) q = q.gte("start_time", from);
  if (to)   q = q.lte("start_time", to);

  const { data, error } = await q;
  if (error) throw error;
  return (data ?? []) as Appointment[];
}

// ─── Waitlist ─────────────────────────────────────────────────────────────────

export async function addToWaitlist(params: {
  business_id: string;
  customer_name: string;
  customer_phone: string;
  requested_date?: string;
  service?: string;
}): Promise<void> {
  const db = createServerClient();
  const { error } = await db.from("waitlist").insert({
    business_id:    params.business_id,
    customer_name:  params.customer_name,
    customer_phone: params.customer_phone,
    requested_date: params.requested_date ?? null,
    service:        params.service ?? null,
  });
  if (error) throw error;
}

async function notifyWaitlist(businessId: string): Promise<void> {
  const db = createServerClient();
  const { data } = await db
    .from("waitlist")
    .select("*")
    .eq("business_id", businessId)
    .eq("notified", false)
    .order("created_at", { ascending: true })
    .limit(1);

  if (!data || data.length === 0) return;

  const entry = data[0] as { id: string; customer_phone: string };

  // Mark as notified (SMS will be sent by the caller)
  await db
    .from("waitlist")
    .update({ notified: true, notified_at: new Date().toISOString() })
    .eq("id", entry.id);

  // Import sms lazily to avoid circular deps
  const { sendSms } = await import("@/services/sms");
  await sendSms(
    entry.customer_phone,
    "Great news! A spot just opened up. Reply BOOK to grab it, or SKIP to stay on the waitlist."
  );
}

// ─── SMS session state ────────────────────────────────────────────────────────

export async function getSession(
  customerPhone: string,
  businessPhone: string
): Promise<Record<string, unknown>> {
  const db = createServerClient();
  const { data } = await db
    .from("sms_sessions")
    .select("state")
    .eq("customer_phone", customerPhone)
    .eq("business_phone", businessPhone)
    .single();
  return (data?.state as Record<string, unknown>) ?? {};
}

export async function saveSession(
  customerPhone: string,
  businessPhone: string,
  state: Record<string, unknown>
): Promise<void> {
  const db = createServerClient();
  await db.from("sms_sessions").upsert(
    {
      customer_phone:  customerPhone,
      business_phone:  businessPhone,
      state,
      last_message_at: new Date().toISOString(),
    },
    { onConflict: "customer_phone,business_phone" }
  );
}

export async function clearSession(
  customerPhone: string,
  businessPhone: string
): Promise<void> {
  await saveSession(customerPhone, businessPhone, {});
}

// ─── Business hours setup ──────────────────────────────────────────────────────

export async function getBusinessHours(businessId: string): Promise<BusinessHours | null> {
  const db = createServerClient();
  const { data } = await db
    .from("business_hours")
    .select("*")
    .eq("business_id", businessId)
    .single();
  return data as BusinessHours | null;
}

export async function upsertBusinessHours(
  businessId: string,
  settings: Partial<Omit<BusinessHours, "id" | "business_id">>
): Promise<void> {
  const db = createServerClient();
  const { error } = await db.from("business_hours").upsert(
    { business_id: businessId, ...settings },
    { onConflict: "business_id" }
  );
  if (error) throw error;
}
