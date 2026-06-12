/**
 * POST /api/generate-site
 *
 * Phase 4: delegates to FORGE engine site_builder.py via POST /build-site.
 * Scoring and CRM normalization remain in Next.js.
 */

import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { requireUserSession } from "@/lib/api-guard";
import { forge } from "@/lib/forge-client";
import { normalize } from "@/services/normalizer";
import { scoreContent } from "@/services/scorer";
import { scoreLeadQuality } from "@/services/lead-quality";
import { getCacheKey, getCached, setCached } from "@/lib/cache";
import type { GenerateSiteResponse, GeneratedContent } from "@/lib/types";

const InputSchema = z.object({
  name: z.string().min(2).max(120),
  location: z.string().min(2).max(100),
  website: z.string().url().optional().or(z.literal("")),
  deploy: z.boolean().optional().default(false),
});

const ipCounts = new Map<string, { count: number; resetAt: number }>();
const FREE_LIMIT = 20;
const WINDOW_MS = 1000 * 60 * 60;

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

function contentFromForge(
  businessName: string,
  serviceType: string,
  city: string
): GeneratedContent {
  return {
    hero: `${businessName} — ${serviceType} in ${city}`,
    subheadline: `Serving ${city} with honest pricing and expert craftsmanship.`,
    services: [],
    cta: "Get Your Free Estimate",
    trust_signals: ["Licensed & Insured", "5-Star Rated", "Same-Day Service"],
    about_snippet: `Locally owned ${serviceType.toLowerCase()} company proudly serving ${city}.`,
  };
}

export async function POST(req: NextRequest) {
  try {
    const session = await requireUserSession(req);
    if (session instanceof NextResponse) return session;

    const body = await req.json();
    const parsed = InputSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { error: parsed.error.issues[0]?.message ?? "Invalid input", code: "INVALID_INPUT" },
        { status: 400 }
      );
    }

    const { name, location, website, deploy } = parsed.data;

    const ip = getClientIp(req);
    if (!checkRateLimit(ip)) {
      return NextResponse.json(
        { error: "Too many requests. Please wait before generating more.", code: "RATE_LIMIT" },
        { status: 429 }
      );
    }

    const cacheKey = getCacheKey(`forge:${name}`, location);
    const cached = getCached(cacheKey);
    if (cached) {
      return NextResponse.json({ ...cached, cached: true });
    }

    let built;
    try {
      built = await forge.buildSite({
        name,
        location,
        website: website || undefined,
        deploy,
      });
    } catch (err) {
      console.error("[generate-site] FORGE build-site failed:", err);
      return NextResponse.json(
        {
          error: "FORGE engine unavailable. Ensure api.py is running and FORGE_API_URL is set.",
          code: "FORGE_ERROR",
        },
        { status: 502 }
      );
    }

    const business = normalize(name, location, {
      phone: built.phone,
    });

    const content = contentFromForge(business.name, business.service_type, business.city);
    const score = scoreContent(content, business);
    const lead_quality = scoreLeadQuality(business);

    const result: GenerateSiteResponse = {
      business,
      content,
      score: { ...score, lead_quality },
      cached: false,
      mode: "forge",
      html: built.html,
      demo_url: built.demo_url ?? undefined,
    };

    setCached(cacheKey, result);
    return NextResponse.json(result, { status: 200 });
  } catch (err) {
    console.error("[generate-site] Unhandled error:", err);
    return NextResponse.json({ error: "Internal server error", code: "FORGE_ERROR" }, { status: 500 });
  }
}