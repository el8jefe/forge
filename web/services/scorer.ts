/**
 * Scoring Engine
 * Evaluates generated content on 4 dimensions without an extra API call.
 * Each dimension is scored 0–10, final score is the average.
 */

import type { GeneratedContent, NormalizedBusiness, ScoreResult, ScoreBreakdown } from "@/lib/types";

// ─── Helpers ──────────────────────────────────────────────────────────────────
const includes = (haystack: string, needle: string) =>
  haystack.toLowerCase().includes(needle.toLowerCase());

const wordCount = (s: string) => s.trim().split(/\s+/).length;

// ─── Dimension Scorers ────────────────────────────────────────────────────────

function scoreClarity(content: GeneratedContent): number {
  let score = 0;

  // Hero is punchy (5-10 words = good; <5 too short; >15 too wordy)
  const hw = wordCount(content.hero);
  if (hw >= 5 && hw <= 10) score += 4;
  else if (hw > 10 && hw <= 14) score += 2;
  else score += 1;

  // Subheadline is informative but not wall-of-text
  const sl = content.subheadline.length;
  if (sl >= 60 && sl <= 200) score += 3;
  else if (sl > 0) score += 1;

  // Services section is populated
  if (content.services.length >= 5) score += 2;
  else if (content.services.length >= 3) score += 1;

  // CTA is short and action-oriented
  const ctaWords = wordCount(content.cta);
  if (ctaWords >= 3 && ctaWords <= 7) score += 1;

  return Math.min(score, 10);
}

function scoreSpecificity(
  content: GeneratedContent,
  business: NormalizedBusiness
): number {
  let score = 0;
  const allText =
    `${content.hero} ${content.subheadline} ${content.about_snippet}`.toLowerCase();

  // City mentioned in the visible copy
  if (business.city && includes(allText, business.city)) score += 4;

  // Service type or trade mentioned in hero/subheadline
  const serviceWords = business.service_type.toLowerCase().split(/\s+/);
  if (serviceWords.some((w) => allText.includes(w))) score += 2;

  // Services are specific (avg description length > 30 chars)
  const avgDescLen =
    content.services.reduce((s, i) => s + i.description.length, 0) /
    Math.max(content.services.length, 1);
  if (avgDescLen >= 40) score += 2;
  else if (avgDescLen >= 20) score += 1;

  // UVPs/trust signals are present
  if (content.trust_signals.length >= 3) score += 2;

  return Math.min(score, 10);
}

function scoreTrust(content: GeneratedContent): number {
  let score = 0;
  const allText =
    `${content.hero} ${content.subheadline} ${content.about_snippet} ${content.trust_signals.join(" ")}`.toLowerCase();

  // Licensing / insurance
  if (includes(allText, "licensed") || includes(allText, "insured")) score += 2;
  if (includes(allText, "bonded")) score += 1;

  // Experience / longevity
  if (
    includes(allText, "years") ||
    includes(allText, "since") ||
    includes(allText, "established")
  )
    score += 2;

  // Guarantee / warranty
  if (includes(allText, "guarantee") || includes(allText, "warranty"))
    score += 2;

  // Has an about snippet (feels human/authentic)
  if (content.about_snippet.length > 80) score += 2;

  // Number of trust signals
  if (content.trust_signals.length >= 4) score += 1;

  return Math.min(score, 10);
}

function scoreConversion(content: GeneratedContent): number {
  let score = 0;
  const allText =
    `${content.hero} ${content.subheadline} ${content.cta}`.toLowerCase();

  // CTA exists and is action-oriented
  if (content.cta.length > 5) score += 2;

  // CTA has a clear action verb
  const actionVerbs = ["call", "get", "request", "schedule", "book", "contact", "claim", "start"];
  if (actionVerbs.some((v) => includes(content.cta, v))) score += 2;

  // CTA includes benefit (free, fast, save)
  const benefitWords = ["free", "fast", "save", "instant", "today", "now"];
  if (benefitWords.some((w) => includes(content.cta, w))) score += 2;

  // Hero has urgency or benefit language
  const urgency = ["today", "now", "fast", "same-day", "emergency", "24/7", "free", "#1", "best", "trusted"];
  if (urgency.some((w) => includes(allText, w))) score += 2;

  // Hero doesn't start with "We" (self-focused is weaker)
  if (!content.hero.toLowerCase().startsWith("we ")) score += 1;

  // About snippet includes a personal connection
  if (
    includes(content.about_snippet, "I ") ||
    includes(content.about_snippet, "our family") ||
    includes(content.about_snippet, "we've")
  )
    score += 1;

  return Math.min(score, 10);
}

// ─── Feedback Builder ─────────────────────────────────────────────────────────
function buildFeedback(score: number, breakdown: ScoreBreakdown): string {
  if (score >= 8.5) return "Excellent — this site is built to convert.";
  if (score >= 7) return "Strong site. A few tweaks will push it over 9.";
  if (score >= 5.5) return "Solid foundation. Key areas need sharpening to compete locally.";
  return "Room to grow — focus on the specific improvements below.";
}

function buildImprovements(
  breakdown: ScoreBreakdown,
  business: NormalizedBusiness
): string[] {
  const tips: string[] = [];

  if (breakdown.clarity < 7) {
    tips.push("Tighten the headline to 6–9 words with a clear benefit.");
  }
  if (breakdown.specificity < 7) {
    tips.push(`Mention "${business.city}" in the hero or subheadline for stronger local relevance.`);
  }
  if (breakdown.trust < 7) {
    tips.push("Add a 'Licensed & Insured' badge and a satisfaction guarantee.");
  }
  if (breakdown.conversion < 7) {
    tips.push("Upgrade the CTA to include urgency: 'Get a Free Quote Today' outperforms 'Contact Us'.");
  }

  if (tips.length === 0) {
    tips.push("Consider adding real customer photos or video testimonials to further boost trust.");
  }

  return tips;
}

// ─── Main Export ──────────────────────────────────────────────────────────────
export function scoreContent(
  content: GeneratedContent,
  business: NormalizedBusiness
): ScoreResult {
  const breakdown: ScoreBreakdown = {
    clarity: scoreClarity(content),
    specificity: scoreSpecificity(content, business),
    trust: scoreTrust(content),
    conversion: scoreConversion(content),
  };

  const avg =
    (breakdown.clarity +
      breakdown.specificity +
      breakdown.trust +
      breakdown.conversion) /
    4;
  const score = Math.round(avg * 10) / 10;

  return {
    score,
    breakdown,
    feedback: buildFeedback(score, breakdown),
    improvements: buildImprovements(breakdown, business),
  };
}
