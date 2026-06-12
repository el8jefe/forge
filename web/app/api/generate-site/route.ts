/**
 * POST /api/generate-site
 *
 * Full pipeline:
 *   Input → Scrape → Normalize → [Template | AI Generate] → Score → LeadQuality → Cache → Return
 */

import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { requireUserSession } from "@/lib/api-guard";
import { scrapeBusinessData } from "@/services/scraper";
import { normalize } from "@/services/normalizer";
import { generateContent } from "@/services/generator";
import { scoreContent } from "@/services/scorer";
import { scoreLeadQuality } from "@/services/lead-quality";
import { generateTemplateHTML } from "@/services/template";
import { getCacheKey, getCached, setCached } from "@/lib/cache";
import type { GenerateSiteResponse } from "@/lib/types";

// ─── Input validation ──────────────────────────────────────────────────────────
const InputSchema = z.object({
  name: z
    .string()
    .min(2, "Business name must be at least 2 characters")
    .max(120, "Business name is too long"),
  location: z
    .string()
    .min(2, "Location must be at least 2 characters")
    .max(100, "Location is too long"),
  mode: z.enum(["template", "ai"]).optional().default("template"),
});

// ─── Rate Limiting (IP-based, in-memory) ──────────────────────────────────────
const ipCounts = new Map<string, { count: number; resetAt: number }>();
const FREE_LIMIT = 20; // requests per window
const WINDOW_MS = 1000 * 60 * 60; // 1 hour

function checkRateLimit(ip: string): boolean {
  const now = Date.now();
  const entry = ipCounts.get(ip);

  if (!entry || now > entry.resetAt) {
    ipCounts.set(ip, { count: 1, resetAt: now + WINDOW_MS });
    return true;
  }

  if (entry.count >= FREE_LIMIT) return false;
  entry.count++;
  return true;
}

function getClientIp(req: NextRequest): string {
  return (
    req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ??
    req.headers.get("x-real-ip") ??
    "unknown"
  );
}

// ─── Handler ──────────────────────────────────────────────────────────────────
export async function POST(req: NextRequest) {
  try {
    const session = await requireUserSession(req);
    if (session instanceof NextResponse) return session;

    // 1. Parse and validate input
    const body = await req.json();
    const parsed = InputSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { error: parsed.error.issues[0]?.message ?? "Invalid input", code: "INVALID_INPUT" },
        { status: 400 }
      );
    }

    const { name, location, mode } = parsed.data;

    // 2. Rate limit check
    const ip = getClientIp(req);
    if (!checkRateLimit(ip)) {
      return NextResponse.json(
        {
          error: "Too many requests. Please wait a bit before generating more.",
          code: "RATE_LIMIT",
        },
        { status: 429 }
      );
    }

    // 3. Cache lookup (keyed by name + location + mode)
    const cacheKey = getCacheKey(`${mode}:${name}`, location);
    const cached = getCached(cacheKey);
    if (cached) {
      return NextResponse.json({ ...cached, cached: true });
    }

    // 4. Scrape (with silent fallback)
    const scraped = await scrapeBusinessData(name, location);

    // 5. Normalize
    const business = normalize(name, location, scraped);

    // 6. Lead quality scoring
    const lead_quality = scoreLeadQuality(business);

    // 7. Template mode — no AI
    if (mode === "template") {
      const html = generateTemplateHTML(business);
      const score = scoreContent(
        {
          hero: `${business.name} — ${business.service_type} in ${business.city}`,
          subheadline: `Serving ${business.city} with honest pricing and expert craftsmanship.`,
          services: [],
          cta: "Get Your Free Estimate",
          trust_signals: ["Licensed & Insured", "5-Star Rated", "Same-Day Service"],
          about_snippet: `Locally owned ${business.service_type.toLowerCase()} company proudly serving ${business.city}.`,
        },
        business
      );

      const result: GenerateSiteResponse = {
        business,
        content: {
          hero: `${business.name} — ${business.service_type} in ${business.city}`,
          subheadline: `Serving ${business.city} with honest pricing and expert craftsmanship.`,
          services: [],
          cta: "Get Your Free Estimate",
          trust_signals: ["Licensed & Insured", "5-Star Rated", "Same-Day Service"],
          about_snippet: `Locally owned ${business.service_type.toLowerCase()} company serving ${business.city}.`,
        },
        score: { ...score, lead_quality },
        cached: false,
        mode: "template",
        html,
      };
      setCached(cacheKey, result);
      return NextResponse.json(result, { status: 200 });
    }

    // 8. AI mode — generate with Claude
    if (!process.env.ANTHROPIC_API_KEY) {
      return NextResponse.json(
        { error: "AI mode is not available — ANTHROPIC_API_KEY is not configured.", code: "AI_ERROR" },
        { status: 503 }
      );
    }

    let content;
    try {
      content = await generateContent(business);
    } catch (err) {
      console.error("[generator] Error:", err);
      return NextResponse.json(
        { error: "AI generation failed. Please try again.", code: "AI_ERROR" },
        { status: 502 }
      );
    }

    // 9. Generate AI-enhanced HTML
    const html = generateTemplateHTML(business, content);

    // 10. Score
    const score = scoreContent(content, business);

    // 11. Build & cache response
    const result: GenerateSiteResponse = {
      business,
      content,
      score: { ...score, lead_quality },
      cached: false,
      mode: "ai",
      html,
    };
    setCached(cacheKey, result);

    return NextResponse.json(result, { status: 200 });
  } catch (err) {
    console.error("[generate-site] Unhandled error:", err);
    return NextResponse.json(
      { error: "Internal server error", code: "AI_ERROR" },
      { status: 500 }
    );
  }
}
