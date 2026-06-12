/**
 * Scraper Service
 * Uses Firecrawl to extract real business data when available.
 * Falls back gracefully — the normalizer + AI generator handle gaps.
 */

interface FirecrawlSearchResult {
  url: string;
  title?: string;
  description?: string;
  markdown?: string;
}

export interface ScrapedData {
  phone?: string;
  email?: string;
  years_in_business?: string;
  services?: string[];
  address?: string;
}

export async function scrapeBusinessData(
  name: string,
  location: string
): Promise<ScrapedData> {
  const apiKey = process.env.FIRECRAWL_API_KEY;
  if (!apiKey) return {};

  try {
    const response = await fetch("https://api.firecrawl.dev/v1/search", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: `${name} ${location} local business phone email services`,
        limit: 3,
        scrapeOptions: { formats: ["markdown"] },
      }),
      signal: AbortSignal.timeout(8000),
    });

    if (!response.ok) return {};

    const data = await response.json();
    const results: FirecrawlSearchResult[] = data.data ?? [];
    if (results.length === 0) return {};

    const combined = results
      .map((r) => r.markdown ?? "")
      .join("\n")
      .slice(0, 8000);

    return extractFromText(combined);
  } catch {
    return {};
  }
}

function extractFromText(text: string): ScrapedData {
  const phone = text.match(/\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/)?.[0];

  const email = text.match(
    /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/
  )?.[0];

  const yearsMatch = text.match(
    /(\d{4}|since\s+\d{4}|established\s+\d{4}|\d+\s+years\s+in\s+business)/i
  )?.[0];

  // Pull bullet-point style services
  const serviceMatches =
    text.match(/[-*•]\s+([A-Z][A-Za-z\s&/,]{3,50}(?=\n|$))/g) ?? [];
  const services = serviceMatches
    .slice(0, 8)
    .map((s) => s.replace(/^[-*•]\s+/, "").trim())
    .filter(Boolean);

  const address = text.match(
    /\d+\s+[A-Z][a-zA-Z\s]+(?:St|Ave|Blvd|Rd|Dr|Ln|Way|Ct)[.,]?\s*\w+/
  )?.[0];

  return {
    phone,
    email,
    years_in_business: yearsMatch,
    services: services.length > 0 ? services : undefined,
    address,
  };
}
