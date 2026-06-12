/**
 * Email Service — Resend
 * Sends outreach emails with a demo site link.
 * Human tone, no spam flags.
 */

import type { OutreachEmailPayload } from "@/lib/types";

export async function sendOutreachEmail(payload: OutreachEmailPayload): Promise<{ success: boolean; error?: string }> {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    return { success: false, error: "RESEND_API_KEY not configured" };
  }

  const { to_email, to_name, business_name, demo_url, service_type, city } = payload;

  const subject = `I built a quick demo site for ${business_name} — take a look?`;
  const html = buildEmailHtml({ business_name, demo_url, service_type, city, to_name });
  const text = buildEmailText({ business_name, demo_url, service_type, city, to_name });

  try {
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: process.env.RESEND_FROM_EMAIL ?? "outreach@tradebuilt.io",
        to: [to_email],
        subject,
        html,
        text,
      }),
      signal: AbortSignal.timeout(10000),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return { success: false, error: (err as { message?: string }).message ?? `HTTP ${res.status}` };
    }

    return { success: true };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : "Unknown error" };
  }
}

// ─── Templates ────────────────────────────────────────────────────────────────
interface TemplateData {
  business_name: string;
  demo_url?: string;
  service_type: string;
  city: string;
  to_name: string;
}

function buildEmailHtml(d: TemplateData): string {
  return `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f9fafb; margin: 0; padding: 0; }
  .wrapper { max-width: 600px; margin: 2rem auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .header { background: linear-gradient(135deg, #0d1b2a, #1a3a5c); padding: 2rem; text-align: center; }
  .header h1 { color: #fff; font-size: 1.5rem; margin: 0; font-weight: 700; letter-spacing: -0.02em; }
  .header p { color: rgba(255,255,255,0.6); margin: 0.5rem 0 0; font-size: 0.9rem; }
  .body { padding: 2rem 2.5rem; }
  .body p { color: #374151; line-height: 1.7; margin: 0 0 1rem; font-size: 0.97rem; }
  .cta-block { background: #f8fafc; border-radius: 10px; padding: 1.5rem; margin: 1.5rem 0; text-align: center; border: 1px solid #e2e8f0; }
  .cta-block p { color: #6b7280; font-size: 0.85rem; margin: 0 0 1rem; }
  .cta-button { display: inline-block; background: #f97316; color: #fff; padding: 0.75rem 2rem; border-radius: 8px; font-weight: 700; font-size: 1rem; text-decoration: none; }
  .footer { padding: 1.5rem 2.5rem; border-top: 1px solid #e2e8f0; }
  .footer p { color: #9ca3af; font-size: 0.8rem; margin: 0; line-height: 1.6; }
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>Hey ${d.to_name.split(" ")[0] ?? d.business_name} 👋</h1>
    <p>I made something for you — takes 30 seconds to check out</p>
  </div>
  <div class="body">
    <p>I was looking for ${d.service_type.toLowerCase()} companies in ${d.city} and noticed <strong>${d.business_name}</strong> could use a stronger online presence.</p>
    <p>So I went ahead and built a free demo site for you — no strings attached. It shows what your business could look like online with modern design and the kind of copy that actually gets people to call.</p>
    ${d.demo_url ? `<div class="cta-block">
      <p>Your free demo site is live at:</p>
      <a href="${d.demo_url}" class="cta-button">View Your Demo Site →</a>
    </div>` : `<div class="cta-block">
      <p>I put together a free demo for <strong>${d.business_name}</strong> — reply to this email and I'll send it over directly.</p>
    </div>`}
    <p>If you like it, I can get this live for you with your real info, photos, and a contact form — for less than you probably spend on coffee this month.</p>
    <p>Worth a quick look. Let me know what you think — reply here or grab a time to chat.</p>
    <p>— Pablo<br><small style="color: #9ca3af;">TradeBuilt · Websites for local trades</small></p>
  </div>
  <div class="footer">
    <p>You're receiving this because your business shows up in local searches for ${d.service_type.toLowerCase()} in ${d.city}. If you'd prefer not to hear from me, just reply "no thanks" and I'll remove you immediately.</p>
  </div>
</div>
</body>
</html>`;
}

function buildEmailText(d: TemplateData): string {
  return `Hey ${d.to_name.split(" ")[0] ?? d.business_name},

I was looking for ${d.service_type.toLowerCase()} companies in ${d.city} and noticed ${d.business_name} could use a stronger online presence.

So I went ahead and built a free demo site for you — no strings attached. It shows what your business could look like online with modern design and copy that actually gets people to call.

${d.demo_url ? `Check it out here: ${d.demo_url}\n\n` : "Reply to this email and I'll send the demo over directly.\n\n"}If you like it, I can get this live for you with your real info, photos, and a contact form — for less than you probably spend on coffee this month.

Worth a quick look. Let me know what you think — just reply here or grab a time to chat.

— Pablo
TradeBuilt · Websites for local trades

---
You're receiving this because your business shows up in local searches for ${d.service_type.toLowerCase()} in ${d.city}. Reply "no thanks" to opt out.`;
}
