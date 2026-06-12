/**
 * Lead Quality Scorer — Layer 2
 * Evaluates how valuable a lead is BEFORE we generate their site.
 * Burning Hot / Hot / Warm / Cold based on business signals.
 */

import type { NormalizedBusiness, LeadQuality, LeadTemperature } from "@/lib/types";

export function scoreLeadQuality(business: NormalizedBusiness): LeadQuality {
  let score = 0;

  const has_phone = Boolean(business.phone);
  const has_email = Boolean(business.email);
  const has_address = Boolean(business.address);
  const has_website = Boolean(business.website);
  const review_count = business.review_count ?? 0;
  const rating = business.rating ?? 0;
  const years_in_business = Boolean(business.years_in_business);

  // ── Contact info completeness (0-30) ──
  if (has_phone) score += 15;
  if (has_email) score += 10;
  if (has_address) score += 5;

  // ── Website quality (0-25) ──
  // No website = GREAT lead (they need us badly)
  // Poor website = good lead
  // Good website = lower priority
  let website_quality: LeadQuality["signals"]["website_quality"] = "none";
  if (!has_website) {
    score += 25; // No website — prime target
    website_quality = "none";
  } else if (has_website) {
    // We don't know quality from normalizer alone, assume "ok" — lower value
    score += 5;
    website_quality = "ok";
  }

  // ── Reviews (0-20) ──
  // Sweet spot: 10-150 reviews. Real business but manageable. >200 = chain or established.
  if (review_count >= 10 && review_count < 50) score += 20;
  else if (review_count >= 50 && review_count < 150) score += 15;
  else if (review_count >= 5 && review_count < 10) score += 10;
  else if (review_count < 5) score += 5; // Very new — might not have budget
  // >150 reviews — established, might not need us as badly
  else score += 5;

  // ── Rating quality (0-15) ──
  if (rating >= 4.5) score += 15;
  else if (rating >= 4.0) score += 10;
  else if (rating >= 3.5) score += 5;
  // Low rating? They need help but might be defensive

  // ── Business completeness (0-10) ──
  if (years_in_business) score += 5; // Established
  if (business.services.length > 0) score += 3; // Has defined services
  if (business.city && business.state) score += 2; // Full location

  score = Math.min(100, score);

  // ── Temperature classification ──
  let temperature: LeadTemperature;
  let temperature_short: LeadQuality["temperature_short"];

  if (score >= 75) {
    temperature = "🔥🔥 Burning Hot";
    temperature_short = "burning";
  } else if (score >= 55) {
    temperature = "🔥 Hot";
    temperature_short = "hot";
  } else if (score >= 35) {
    temperature = "🌡️ Warm";
    temperature_short = "warm";
  } else {
    temperature = "❄️ Cold";
    temperature_short = "cold";
  }

  // ── Human-readable reason ──
  const reasons: string[] = [];
  if (!has_website) reasons.push("no website (prime target)");
  if (has_phone && has_email) reasons.push("full contact info");
  else if (has_phone) reasons.push("phone only");
  if (review_count > 0) reasons.push(`${review_count} reviews`);
  if (rating > 0) reasons.push(`★ ${rating}`);
  if (!has_phone && !has_email) reasons.push("contact info missing");

  const reason = reasons.length > 0 ? reasons.join(", ") : "minimal data available";

  return {
    temperature,
    temperature_short,
    lead_score: score,
    signals: {
      has_phone,
      has_email,
      has_address,
      has_website,
      website_quality,
      review_count,
      rating,
      years_in_business,
    },
    reason,
  };
}
