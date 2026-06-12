/**
 * SMS Service — Twilio
 * Sends outbound SMS messages.
 * Requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER in .env.local
 */

export async function sendSms(to: string, body: string): Promise<{ success: boolean; error?: string }> {
  const accountSid = process.env.TWILIO_ACCOUNT_SID;
  const authToken  = process.env.TWILIO_AUTH_TOKEN;
  const from       = process.env.TWILIO_PHONE_NUMBER;

  if (!accountSid || !authToken || !from) {
    console.warn("[sms] Twilio not configured — skipping SMS to", to);
    return { success: false, error: "Twilio not configured" };
  }

  try {
    const res = await fetch(
      `https://api.twilio.com/2010-04-01/Accounts/${accountSid}/Messages.json`,
      {
        method: "POST",
        headers: {
          Authorization: "Basic " + Buffer.from(`${accountSid}:${authToken}`).toString("base64"),
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({ To: to, From: from, Body: body }).toString(),
        signal: AbortSignal.timeout(10000),
      }
    );

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return { success: false, error: (err as { message?: string }).message ?? `HTTP ${res.status}` };
    }

    return { success: true };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : "Unknown error" };
  }
}
