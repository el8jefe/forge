/**
 * AI Content Generator
 * Uses Claude Haiku to produce high-converting website copy.
 * Structured output guarantees a clean JSON response every time.
 */

import Anthropic from "@anthropic-ai/sdk";
import { z } from "zod";
import type { NormalizedBusiness, GeneratedContent } from "@/lib/types";

// ─── Output Schema ────────────────────────────────────────────────────────────
const ServiceItemSchema = z.object({
  name: z.string(),
  description: z.string(),
  icon: z.string(),
});

const ContentSchema = z.object({
  hero: z.string(),
  subheadline: z.string(),
  services: z.array(ServiceItemSchema).min(4).max(8),
  cta: z.string(),
  trust_signals: z.array(z.string()).min(3).max(5),
  about_snippet: z.string(),
});

// ─── Prompt Builder ───────────────────────────────────────────────────────────
function buildPrompt(biz: NormalizedBusiness): string {
  const hasServices =
    biz.services.length > 0 ? biz.services.join(", ") : "not specified";

  return `You are writing the website copy for a real local business.

Business: ${biz.name}
Service Type: ${biz.service_type}
Location: ${biz.city}${biz.state ? `, ${biz.state}` : ""}
Services Known: ${hasServices}
Brand Tone: ${biz.tone}
Key Differentiators: ${biz.unique_value_props.join("; ")}
${biz.years_in_business ? `Years in Business: ${biz.years_in_business}` : ""}
${biz.phone ? `Phone: ${biz.phone}` : ""}

Generate high-converting website content. Return ONLY valid JSON matching this schema exactly:

{
  "hero": "string — punchy 5-9 word headline. MUST reference the service or a core benefit. Do NOT start with 'We'. Must feel like it was written for THIS city.",
  "subheadline": "string — 1-2 sentences that mention ${biz.city} by name, explain what makes this business different, and hint at a key benefit for the customer.",
  "services": [
    { "name": "string", "description": "string — one compelling sentence explaining the value", "icon": "string — service name keyword, e.g. 'hvac', 'plumbing', 'electrical', 'roofing', 'painting', 'pest', 'cleaning', 'landscaping', 'concrete'" }
  ],
  "cta": "string — 4-7 word call to action. Should include a benefit or urgency (e.g. 'Get Your Free Quote Today' or 'Call for Same-Day Service').",
  "trust_signals": ["string — short trust statements, e.g. 'Licensed & Insured in ${biz.state || "your state"}', 'Family-Owned Since 2009', '500+ Happy Customers'"],
  "about_snippet": "string — 2-3 sentences written in first person as the business owner. Mention ${biz.city} and sound like a real local professional, not a corporate template."
}

Rules:
- NEVER use bracket placeholders like [City] or [Business Name] — always fill them in
- NEVER use emojis anywhere in the output — not in hero, subheadline, services, cta, trust_signals, or about_snippet
- The icon field must be a short lowercase keyword (e.g. "hvac", "drain", "roof") — not an emoji
- Generate 5-7 services appropriate for this ${biz.service_type} business in ${biz.city}
- If services were provided, include them; supplement with other realistic services
- The hero must feel specific, not generic ("Fast HVAC Repair in Denver" beats "Quality Service You Can Trust")
- Make trust_signals credible and local (mention the state, certifications common in this trade)
- The about_snippet should feel human — mention the city, something about the owner's commitment`;
}

// ─── Main Export ──────────────────────────────────────────────────────────────
export async function generateContent(
  business: NormalizedBusiness
): Promise<GeneratedContent> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error("ANTHROPIC_API_KEY is not configured");
  }

  const client = new Anthropic({ apiKey });

  const response = await client.messages.create({
    model: "claude-haiku-4-5-20251001",
    max_tokens: 2000,
    system:
      "You are an expert copywriter specializing in local service business websites. You write clear, specific, conversion-focused copy that speaks directly to homeowners. You always return pure JSON with no markdown fences or extra text.",
    messages: [
      {
        role: "user",
        content: buildPrompt(business),
      },
    ],
  });

  // Extract text from response (thinking blocks come first, text block last)
  const textBlock = response.content.find((b) => b.type === "text");
  if (!textBlock || textBlock.type !== "text") {
    throw new Error("No text content in Claude response");
  }

  // Strip any accidental markdown fences
  const raw = textBlock.text.replace(/^```(?:json)?\s*/m, "").replace(/```\s*$/m, "").trim();

  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new Error(`Claude returned invalid JSON: ${raw.slice(0, 200)}`);
  }

  const validated = ContentSchema.safeParse(parsed);
  if (!validated.success) {
    throw new Error(
      `Content validation failed: ${validated.error.message}`
    );
  }

  return validated.data;
}
