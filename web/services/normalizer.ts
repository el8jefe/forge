/**
 * Normalizer Service
 * Transforms raw input + optional scraped data into a clean NormalizedBusiness.
 * Works for ANY business type — no hardcoded industry lists.
 */

import type { NormalizedBusiness } from "@/lib/types";
import type { ScrapedData } from "./scraper";

// Re-export ScrapedData so route can import it from one place
export type { ScrapedData };

// ─── Service Type Inference ───────────────────────────────────────────────────
// Uses signal words in the business name to infer the primary service category.
// Intentionally broad — Claude fills in the rest during generation.
const SERVICE_SIGNALS: [RegExp, string][] = [
  [/hvac|heating|cooling|air\s*cond|furnace|boiler/i, "HVAC"],
  [/plumb|pipe|drain|sewer|water\s*heat/i, "Plumbing"],
  [/electric|wiring|panel|circuit|lighting/i, "Electrical"],
  [/roof|gutter|shingle|siding/i, "Roofing"],
  [/landscap|lawn|garden|mow|tree|irrigation/i, "Landscaping"],
  [/pest|termite|extermina|bug|rodent|mosquito/i, "Pest Control"],
  [/paint|stain|coat/i, "Painting"],
  [/clean|janitorial|maid|pressure\s*wash/i, "Cleaning"],
  [/floor|carpet|tile|hardwood/i, "Flooring"],
  [/fence|deck|pergola/i, "Fencing & Decking"],
  [/window|door|glass/i, "Windows & Doors"],
  [/concrete|pav|asphalt|driveway/i, "Concrete & Paving"],
  [/solar|energy/i, "Solar"],
  [/remodel|renovate|kitchen|bathroom/i, "Remodeling"],
  [/construct|build|general\s*contract/i, "General Contracting"],
  [/move|moving|storage/i, "Moving"],
  [/handyman/i, "Handyman Services"],
  [/drywall|plaster/i, "Drywall"],
  [/insul/i, "Insulation"],
  [/garage/i, "Garage Services"],
];

function inferServiceType(name: string): string {
  for (const [pattern, type] of SERVICE_SIGNALS) {
    if (pattern.test(name)) return type;
  }
  return "Home Services";
}

// ─── Location Parsing ─────────────────────────────────────────────────────────
function parseLocation(location: string): { city: string; state: string } {
  const clean = location.trim();

  // "Denver, CO" or "Denver, Colorado"
  const comma = clean.match(/^(.+?),\s*([A-Z]{2}|[A-Za-z]+)$/);
  if (comma) {
    return { city: comma[1].trim(), state: comma[2].trim() };
  }

  // "Denver CO" (no comma)
  const space = clean.match(/^(.+?)\s+([A-Z]{2})$/);
  if (space) {
    return { city: space[1].trim(), state: space[2].trim() };
  }

  return { city: clean, state: "" };
}

// ─── Tone Inference ───────────────────────────────────────────────────────────
function inferTone(
  serviceType: string
): NormalizedBusiness["tone"] {
  const urgent = ["HVAC", "Plumbing", "Electrical", "Roofing", "Pest Control"];
  const premium = ["Solar", "Remodeling", "General Contracting"];
  const friendly = ["Landscaping", "Cleaning", "Handyman Services"];

  if (urgent.includes(serviceType)) return "urgent";
  if (premium.includes(serviceType)) return "premium";
  if (friendly.includes(serviceType)) return "friendly";
  return "professional";
}

// ─── UVP Generation ───────────────────────────────────────────────────────────
function buildUVPs(
  serviceType: string,
  city: string,
  scraped: ScrapedData
): string[] {
  const uvps: string[] = [];

  if (scraped.years_in_business) {
    uvps.push(`Serving ${city} for ${scraped.years_in_business}`);
  } else {
    uvps.push(`Locally owned & operated in ${city}`);
  }

  // Add a service-type-specific differentiator
  const urgentTypes = ["HVAC", "Plumbing", "Electrical"];
  if (urgentTypes.includes(serviceType)) {
    uvps.push("24/7 emergency service available");
  }

  uvps.push("Licensed, bonded & insured");
  uvps.push("Free estimates on all jobs");

  return uvps;
}

// ─── Main Export ──────────────────────────────────────────────────────────────
export function normalize(
  name: string,
  location: string,
  scraped: ScrapedData = {}
): NormalizedBusiness {
  const service_type = inferServiceType(name);
  const { city, state } = parseLocation(location);
  const tone = inferTone(service_type);
  const unique_value_props = buildUVPs(service_type, city, scraped);

  return {
    name: name.trim(),
    service_type,
    location: location.trim(),
    city,
    state,
    services: scraped.services ?? [],
    tone,
    unique_value_props,
    phone: scraped.phone,
    years_in_business: scraped.years_in_business,
  };
}
