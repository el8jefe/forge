/**
 * Template Generator — FREE Tier
 * Produces a full single-page site from business data.
 * No emojis. SVG icons. Professional design.
 */

import type { NormalizedBusiness, GeneratedContent } from "@/lib/types";
import { getTheme } from "@/lib/themes";

// ─── SVG icon library (inline, viewBox 0 0 24 24, stroke style) ───────────────
const ICONS: Record<string, string> = {
  wrench:    `<path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z" stroke-linecap="round" stroke-linejoin="round"/>`,
  flame:     `<path d="M12 2c0 0-4 6-4 10a4 4 0 008 0c0-2-1-4-1-4s-1 2-2 3c-1-2-1-9-1-9z" stroke-linecap="round" stroke-linejoin="round"/>`,
  snowflake: `<line x1="12" y1="2" x2="12" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2l-3 3m3-3l3 3M12 22l-3-3m3 3l3-3M2 12l3-3m-3 3l3 3M22 12l-3-3m3 3l-3 3"/>`,
  droplet:   `<path d="M12 2L5 12a7 7 0 0014 0z" stroke-linecap="round" stroke-linejoin="round"/>`,
  zap:       `<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" stroke-linecap="round" stroke-linejoin="round"/>`,
  home:      `<path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" stroke-linecap="round" stroke-linejoin="round"/><polyline points="9 22 9 12 15 12 15 22" stroke-linecap="round" stroke-linejoin="round"/>`,
  building:  `<rect x="4" y="2" width="16" height="20" rx="2"/><line x1="9" y1="6" x2="9" y2="6"/><line x1="15" y1="6" x2="15" y2="6"/><line x1="9" y1="10" x2="9" y2="10"/><line x1="15" y1="10" x2="15" y2="10"/><line x1="9" y1="14" x2="9" y2="14"/><line x1="15" y1="14" x2="15" y2="14"/><line x1="9" y1="18" x2="15" y2="18"/>`,
  shield:    `<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke-linecap="round" stroke-linejoin="round"/>`,
  clock:     `<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14" stroke-linecap="round"/>`,
  clipboard: `<path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>`,
  check:     `<polyline points="20 6 9 17 4 12" stroke-linecap="round" stroke-linejoin="round"/>`,
  leaf:      `<path d="M2 22c0 0 4-8 12-10S22 2 22 2s-2 8-10 12S2 22 2 22z" stroke-linecap="round" stroke-linejoin="round"/>`,
  scissors:  `<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/>`,
  sun:       `<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>`,
  tool:      `<path d="M3 21l9-9"/><path d="M12.22 6.22a5.5 5.5 0 016.4 7.11l-1.62-1.62-2.83 2.83 1.62 1.62A5.5 5.5 0 016.68 9.6l2.83 2.83 2.83-2.83L10.22 7.4"/>`,
  paint:     `<path d="M19 3H5a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2z"/><path d="M3 15h4v4H3z"/><line x1="10" y1="15" x2="10" y2="19"/><line x1="14" y1="15" x2="14" y2="19"/>`,
  layers:    `<polygon points="12 2 2 7 12 12 22 7 12 2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="2 17 12 22 22 17" stroke-linecap="round" stroke-linejoin="round"/><polyline points="2 12 12 17 22 12" stroke-linecap="round" stroke-linejoin="round"/>`,
  phone:     `<path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07A19.5 19.5 0 013.07 9.8a19.79 19.79 0 01-3.07-8.63A2 2 0 012 .18h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L6.09 7.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 14v2.92z" stroke-linecap="round" stroke-linejoin="round"/>`,
  star:      `<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" stroke-linecap="round" stroke-linejoin="round"/>`,
  truck:     `<rect x="1" y="3" width="15" height="13" rx="1"/><path d="M16 8h4l3 4v4h-7V8z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>`,
  hammer:    `<path d="M15 12l-8.5 8.5c-.83.83-2.17.83-3 0 0 0 0 0 0 0a2.12 2.12 0 010-3L12 9" stroke-linecap="round" stroke-linejoin="round"/><path d="M17.64 15L22 10.64" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.91 11.7l-1.25-1.25c-.6-.6-.93-1.4-.93-2.25v-.86L16.01 4.6a5.56 5.56 0 00-3.94-1.64H9l.92.82A6.18 6.18 0 0112 8.4v1.56l2 2h2.47l2.26 1.91" stroke-linecap="round" stroke-linejoin="round"/>`,
};

// Pick icon for a service name
function iconForService(name: string): string {
  const n = name.toLowerCase();
  if (n.includes("heat") || n.includes("furnace") || n.includes("boiler")) return ICONS.flame;
  if (n.includes("cool") || n.includes("ac") || n.includes("air") || n.includes("refriger")) return ICONS.snowflake;
  if (n.includes("water") || n.includes("drain") || n.includes("pipe") || n.includes("leak") || n.includes("plumb") || n.includes("sewer")) return ICONS.droplet;
  if (n.includes("electric") || n.includes("panel") || n.includes("wir") || n.includes("outlet") || n.includes("circuit") || n.includes("ev") || n.includes("charger")) return ICONS.zap;
  if (n.includes("roof") || n.includes("shingle") || n.includes("gutter") || n.includes("storm")) return ICONS.layers;
  if (n.includes("lawn") || n.includes("grass") || n.includes("mow")) return ICONS.scissors;
  if (n.includes("tree") || n.includes("shrub") || n.includes("plant") || n.includes("landscape") || n.includes("garden") || n.includes("leaf") || n.includes("mulch")) return ICONS.leaf;
  if (n.includes("paint") || n.includes("coat") || n.includes("stain")) return ICONS.paint;
  if (n.includes("emerg") || n.includes("24/7") || n.includes("urgent") || n.includes("same-day") || n.includes("same day")) return ICONS.clock;
  if (n.includes("inspect") || n.includes("estimat") || n.includes("quote") || n.includes("assess")) return ICONS.clipboard;
  if (n.includes("insur") || n.includes("instal") || n.includes("replac") || n.includes("new")) return ICONS.shield;
  if (n.includes("resid") || n.includes("home") || n.includes("house")) return ICONS.home;
  if (n.includes("commercial") || n.includes("business") || n.includes("office")) return ICONS.building;
  if (n.includes("repair") || n.includes("fix") || n.includes("service") || n.includes("maintain") || n.includes("tune")) return ICONS.wrench;
  if (n.includes("clean") || n.includes("wash") || n.includes("pressure") || n.includes("power")) return ICONS.sun;
  if (n.includes("haul") || n.includes("remov") || n.includes("demolit") || n.includes("debris")) return ICONS.truck;
  if (n.includes("pest") || n.includes("termit") || n.includes("rodent") || n.includes("bug")) return ICONS.shield;
  if (n.includes("concr") || n.includes("driveway") || n.includes("patio") || n.includes("foundati")) return ICONS.hammer;
  return ICONS.tool;
}

function svgIcon(paths: string, color: string): string {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="1.75" aria-hidden="true">${paths}</svg>`;
}

// ─── Default service content by trade ─────────────────────────────────────────
const DEFAULT_SERVICES: Record<string, Array<{ name: string; description: string }>> = {
  hvac: [
    { name: "AC Installation",      description: "Energy-efficient systems sized for your home, installed cleanly and correctly the first time." },
    { name: "Heating Repair",        description: "Fast diagnosis and lasting repair for furnaces, heat pumps, and boilers of any brand." },
    { name: "System Tune-Up",        description: "Annual maintenance that keeps efficiency high, extends equipment life, and prevents breakdowns." },
    { name: "Duct Cleaning",         description: "Remove buildup from your ductwork to improve air quality and system performance." },
    { name: "Emergency Service",     description: "Around-the-clock emergency response — we pick up the phone and show up fast." },
    { name: "Free Estimates",        description: "Written, no-obligation quotes on all installations and major repairs. No surprises on the invoice." },
  ],
  plumbing: [
    { name: "Drain Cleaning",        description: "Clear stubborn clogs with professional hydro-jetting and snaking — no temporary fixes." },
    { name: "Water Heater Service",  description: "Installation, repair, and replacement for tank and tankless water heaters of any brand." },
    { name: "Leak Detection",        description: "Advanced detection to find hidden leaks before they cause thousands in damage." },
    { name: "Bathroom Plumbing",     description: "Fixture installation, toilet repair, shower upgrades, and everything in between." },
    { name: "Emergency Plumbing",    description: "24-hour response for burst pipes, flooding, sewage backups, and water emergencies." },
    { name: "Free Estimates",        description: "Honest, upfront pricing with no hidden fees. You approve the cost before we start." },
  ],
  electrical: [
    { name: "Panel Upgrades",        description: "Electrical panel upgrades and replacements to handle modern power demands safely." },
    { name: "Outlet & Wiring",       description: "New outlets, rewiring, and electrical code compliance work done to permit standards." },
    { name: "EV Charger Install",    description: "Level 2 home EV charging station installation with full permitting and inspection." },
    { name: "Surge Protection",      description: "Whole-home surge protection to safeguard appliances, electronics, and HVAC systems." },
    { name: "Emergency Electric",    description: "24-hour emergency response for outages, sparking, and electrical hazards." },
    { name: "Free Estimates",        description: "Detailed written estimates with no pressure. You see the cost before a single wire is touched." },
  ],
  roofing: [
    { name: "Roof Replacement",      description: "Complete asphalt, metal, and tile roof replacement with manufacturer warranty and workmanship guarantee." },
    { name: "Storm Damage Repair",   description: "Insurance-approved storm damage restoration — we help you through the claims process." },
    { name: "Roof Inspection",       description: "Thorough inspections with photo documentation and detailed reports at no cost." },
    { name: "Leak Repair",           description: "Accurate leak detection and permanent waterproof repairs that hold through any weather." },
    { name: "Gutter Services",       description: "Seamless gutter installation, cleaning, and guard systems to protect your foundation." },
    { name: "Free Estimates",        description: "No-obligation quotes with transparent line-item pricing and insurance claim support." },
  ],
  landscaping: [
    { name: "Lawn Maintenance",      description: "Consistent weekly service — mowing, edging, trimming, and blowing for a pristine property." },
    { name: "Tree & Shrub Care",     description: "Expert pruning, shaping, and removal to promote healthy growth and strong structure." },
    { name: "Irrigation Systems",    description: "Smart irrigation installation, repair, and seasonal adjustments that conserve water and reduce bills." },
    { name: "Landscape Design",      description: "Custom design plans that transform your outdoor space into something you actually enjoy." },
    { name: "Seasonal Cleanup",      description: "Spring and fall cleanup, leaf removal, aeration, and mulch application to prepare your yard." },
    { name: "Free Estimates",        description: "Free property walkthrough and detailed quote with no obligation to book." },
  ],
  painting: [
    { name: "Interior Painting",     description: "Clean, precise interior painting with thorough prep work and minimal disruption to your home." },
    { name: "Exterior Painting",     description: "Long-lasting exterior coatings with proper surface prep, priming, and premium paint." },
    { name: "Cabinet Refinishing",   description: "Transform your kitchen cabinets without a full replacement — fraction of the cost." },
    { name: "Deck & Fence Staining", description: "Staining and sealing to protect and restore wood surfaces for years of use." },
    { name: "Drywall Repair",        description: "Seamless drywall patching and repair before any painting begins." },
    { name: "Free Estimates",        description: "Detailed written quotes with no pressure. See the cost before we open a single can." },
  ],
  concrete: [
    { name: "Driveway Replacement",  description: "New concrete driveways poured to spec with proper base preparation and finishing." },
    { name: "Patio Installation",    description: "Custom patio slabs, stamped concrete, and decorative finishes for outdoor living." },
    { name: "Foundation Repair",     description: "Crack repair, leveling, and waterproofing to protect your home's structural integrity." },
    { name: "Sidewalk & Curb",       description: "ADA-compliant sidewalk installation and curb replacement for residential and commercial." },
    { name: "Decorative Concrete",   description: "Stamped, stained, and polished concrete that combines durability with great looks." },
    { name: "Free Estimates",        description: "On-site assessment and written quote at no cost. No obligation, no pressure." },
  ],
  pest: [
    { name: "General Pest Control",  description: "Comprehensive interior and exterior treatment for ants, roaches, spiders, and common pests." },
    { name: "Termite Treatment",     description: "Liquid and baiting termite elimination with structural protection warranties." },
    { name: "Rodent Exclusion",      description: "Identification, trapping, and permanent entry-point sealing to keep rodents out." },
    { name: "Bed Bug Treatment",     description: "Heat and chemical treatment protocols that eliminate bed bugs at every life stage." },
    { name: "Quarterly Service",     description: "Scheduled quarterly treatments to maintain a pest-free home year-round." },
    { name: "Free Inspection",       description: "Free property inspection with written findings and a treatment recommendation." },
  ],
  cleaning: [
    { name: "Regular Cleaning",      description: "Consistent weekly or biweekly home cleaning with the same trusted team every visit." },
    { name: "Deep Cleaning",         description: "Top-to-bottom deep clean for move-ins, move-outs, or spring cleaning." },
    { name: "Post-Construction",     description: "Thorough debris and dust removal after renovation or new construction." },
    { name: "Office Cleaning",       description: "Professional commercial cleaning scheduled around your business hours." },
    { name: "Carpet Cleaning",       description: "Hot water extraction carpet cleaning that removes deep-set stains and allergens." },
    { name: "Free Estimates",        description: "Free walkthrough quote based on your actual space. No hourly surprises." },
  ],
  default: [
    { name: "Quality Workmanship",   description: "Every job done right the first time with attention to detail that shows in the finished product." },
    { name: "Expert Repairs",        description: "Experienced technicians who diagnose accurately and fix it properly — not just temporarily." },
    { name: "Residential Service",   description: "Trusted by homeowners throughout the area for reliable, respectful service." },
    { name: "Commercial Service",    description: "Commercial and multi-unit property services available on flexible scheduling." },
    { name: "Emergency Response",    description: "Fast response times when you need help urgently — we answer the phone." },
    { name: "Free Estimates",        description: "Written estimates with line-item pricing before any work begins. No hidden charges." },
  ],
};

function getDefaultServices(serviceType: string) {
  const st = serviceType.toLowerCase();
  for (const [key, services] of Object.entries(DEFAULT_SERVICES)) {
    if (key === "default") continue;
    if (st.includes(key) || key.includes(st.split(" ")[0])) return services;
  }
  // fuzzy match on keywords
  if (st.includes("hvac") || st.includes("heat") || st.includes("cool") || st.includes("air")) return DEFAULT_SERVICES.hvac;
  if (st.includes("plumb") || st.includes("pipe") || st.includes("water")) return DEFAULT_SERVICES.plumbing;
  if (st.includes("electric")) return DEFAULT_SERVICES.electrical;
  if (st.includes("roof")) return DEFAULT_SERVICES.roofing;
  if (st.includes("landscape") || st.includes("lawn") || st.includes("tree")) return DEFAULT_SERVICES.landscaping;
  if (st.includes("paint")) return DEFAULT_SERVICES.painting;
  if (st.includes("concr") || st.includes("driveway") || st.includes("patio")) return DEFAULT_SERVICES.concrete;
  if (st.includes("pest") || st.includes("termit") || st.includes("extermina")) return DEFAULT_SERVICES.pest;
  if (st.includes("clean") || st.includes("maid") || st.includes("janitor")) return DEFAULT_SERVICES.cleaning;
  return DEFAULT_SERVICES.default;
}

const TESTIMONIALS = [
  { name: "Sarah M.",    stars: 5, text: "Incredibly professional and fast. Showed up on time, explained everything clearly, and the work was flawless. Highly recommend to anyone in the area." },
  { name: "Robert K.",   stars: 5, text: "Best experience I have had with a contractor in years. Fair price, great communication, and they cleaned up completely when done. Will absolutely use again." },
  { name: "Jennifer L.", stars: 5, text: "Called for an emergency and they were at my door within the hour. Fixed the problem and caught something else I was not aware of. Could not ask for better service." },
];

// ─── Booking Widget HTML ───────────────────────────────────────────────────────
// Injected into Pro (AI-mode) sites only. business._bookingBusinessId must be set.

function bookingWidgetHtml(business: NormalizedBusiness & { _bookingBusinessId?: string; _apiBase?: string }, content?: GeneratedContent): string {
  const services = content?.services?.map(s => s.name) ?? business.services ?? [];
  const serviceOptions = services.map(s => `<option value="${s}">${s}</option>`).join("");
  const apiBase = business._apiBase ?? "https://tradebuilt.io";
  const bizId   = business._bookingBusinessId ?? "";

  return `
  <!-- BOOKING SECTION -->
  <section class="section" id="booking" style="background:#f8fafc;">
    <div class="section-inner">
      <div class="fade-in" style="text-align:center;margin-bottom:2.5rem;">
        <p class="section-label">AI Scheduling</p>
        <h2 class="section-title">Book your appointment online</h2>
        <p class="section-sub">Pick a time that works for you. You'll get a confirmation text immediately.</p>
      </div>
      <div class="fade-in" style="max-width:600px;margin:0 auto;">
        <div style="background:#fff;border-radius:16px;padding:2rem;box-shadow:0 2px 20px rgba(0,0,0,0.06);border:1px solid #e5e7eb;">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:1.5rem;padding-bottom:1.5rem;border-bottom:1px solid #f3f4f6;">
            <div style="width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,#f97316,#ea580c);display:flex;align-items:center;justify-content:center;flex-shrink:0;">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
            </div>
            <div>
              <p style="font-weight:800;font-size:15px;color:#111827;margin:0;">Schedule online — 24/7</p>
              <p style="font-size:13px;color:#6b7280;margin:0;">No phone tag. Pick your time and get confirmed instantly.</p>
            </div>
          </div>
          <button id="tb-fab" style="width:100%;padding:14px;background:linear-gradient(135deg,#f97316,#ea580c);color:#fff;font-size:15px;font-weight:800;border:none;border-radius:12px;cursor:pointer;letter-spacing:-0.02em;display:flex;align-items:center;justify-content:center;gap:8px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            Pick a Time
          </button>
          <p style="text-align:center;font-size:12px;color:#9ca3af;margin:12px 0 0;">Or text us to book: ${business.phone ?? "(your number)"}</p>
        </div>
      </div>
    </div>
  </section>

  <!-- BOOKING MODAL -->
  <div id="tb-booking-widget" data-api="${apiBase}" data-bid="${bizId}" style="display:none;"></div>

  <div id="tb-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.55);z-index:9999;align-items:center;justify-content:center;padding:16px;">
    <div style="background:#fff;border-radius:20px;width:100%;max-width:480px;max-height:90vh;overflow-y:auto;position:relative;box-shadow:0 24px 80px rgba(0,0,0,0.25);">

      <!-- Modal header -->
      <div style="padding:20px 24px 16px;border-bottom:1px solid #f3f4f6;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;background:#fff;border-radius:20px 20px 0 0;z-index:1;">
        <div>
          <p style="font-weight:900;font-size:16px;color:#111827;margin:0;letter-spacing:-0.02em;">Book an Appointment</p>
          <p style="font-size:12px;color:#9ca3af;margin:0;">${business.name}</p>
        </div>
        <button id="tb-close" style="width:32px;height:32px;border-radius:50%;background:#f9fafb;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2.5" stroke-linecap="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <!-- Loading -->
      <div id="tb-loading" style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:60px 24px;gap:16px;">
        <div style="width:40px;height:40px;border-radius:50%;border:3px solid #f97316;border-top-color:transparent;animation:tb-spin 0.8s linear infinite;"></div>
        <p style="font-size:14px;color:#6b7280;margin:0;">Loading available times…</p>
      </div>

      <!-- Date + Time Picker -->
      <div id="tb-picker" style="display:none;padding:20px 24px;">
        <p style="font-size:12px;font-weight:700;color:#9ca3af;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 12px;">Select a date</p>
        <div id="tb-dates" style="display:flex;gap:8px;overflow-x:auto;padding-bottom:8px;margin-bottom:20px;"></div>

        <p style="font-size:12px;font-weight:700;color:#9ca3af;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 12px;">Available times</p>
        <div id="tb-no-slots" style="display:none;background:#fef9f0;border:1px solid #fed7aa;border-radius:10px;padding:14px;font-size:13px;color:#9a3412;margin-bottom:16px;">
          No availability found. Please call us to schedule.
        </div>
        <div id="tb-times" style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:24px;min-height:40px;"></div>

        <button id="tb-next" disabled style="width:100%;padding:13px;background:#f97316;color:#fff;font-weight:800;font-size:14px;border:none;border-radius:12px;cursor:pointer;opacity:0.4;transition:opacity 0.15s;" onmouseenter="if(!this.disabled)this.style.opacity='0.9'" onmouseleave="if(!this.disabled)this.style.opacity='1'">
          Continue →
        </button>
      </div>

      <!-- Form -->
      <div id="tb-form" style="display:none;padding:20px 24px;">
        <div style="background:#f8fafc;border-radius:12px;padding:12px 16px;margin-bottom:20px;font-size:13px;color:#374151;">
          <strong>Selected:</strong> <span id="tb-slot-label"></span>
        </div>
        <form id="tb-booking-form">
          <div style="margin-bottom:14px;">
            <label style="display:block;font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Your name</label>
            <input id="tb-name" type="text" required placeholder="John Smith" style="width:100%;box-sizing:border-box;padding:11px 14px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;font-size:14px;color:#111827;outline:none;">
          </div>
          <div style="margin-bottom:14px;">
            <label style="display:block;font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Phone number</label>
            <input id="tb-phone" type="tel" required placeholder="(303) 555-0123" style="width:100%;box-sizing:border-box;padding:11px 14px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;font-size:14px;color:#111827;outline:none;">
            <p style="font-size:11px;color:#9ca3af;margin:4px 0 0;">You'll get a confirmation text at this number.</p>
          </div>
          ${serviceOptions ? `<div style="margin-bottom:20px;">
            <label style="display:block;font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Service needed</label>
            <select id="tb-service" style="width:100%;box-sizing:border-box;padding:11px 14px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;font-size:14px;color:#111827;outline:none;">
              <option value="">Select a service…</option>${serviceOptions}
            </select>
          </div>` : ""}
          <button id="tb-submit" type="submit" style="width:100%;padding:13px;background:linear-gradient(135deg,#f97316,#ea580c);color:#fff;font-weight:800;font-size:14px;border:none;border-radius:12px;cursor:pointer;">
            Confirm Booking
          </button>
        </form>
        <button id="tb-back" style="width:100%;margin-top:10px;padding:10px;background:none;border:none;font-size:13px;color:#9ca3af;cursor:pointer;">← Back to times</button>
      </div>

      <!-- Confirmation -->
      <div id="tb-confirm" style="display:none;padding:40px 24px;text-align:center;">
        <div style="width:56px;height:56px;border-radius:50%;background:#dcfce7;display:flex;align-items:center;justify-content:center;margin:0 auto 20px;">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </div>
        <h3 style="font-weight:900;font-size:20px;color:#111827;letter-spacing:-0.03em;margin:0 0 8px;">You're booked!</h3>
        <p style="font-size:14px;color:#6b7280;margin:0 0 6px;">Appointment confirmed for <strong id="tb-confirm-name"></strong></p>
        <p style="font-size:14px;color:#374151;font-weight:600;margin:0 0 24px;" id="tb-confirm-time"></p>
        <p style="font-size:12px;color:#9ca3af;margin:0 0 24px;">A confirmation text has been sent to your phone.</p>
        <button id="tb-done" style="padding:12px 32px;background:#111827;color:#fff;font-weight:700;font-size:14px;border:none;border-radius:12px;cursor:pointer;">Done</button>
      </div>
    </div>
  </div>

  <style>
    .tb-date-btn { display:flex;flex-direction:column;align-items:center;gap:4px;min-width:52px;padding:10px 8px;background:#f9fafb;border:1.5px solid #e5e7eb;border-radius:12px;cursor:pointer;font-family:inherit;transition:all 0.15s; }
    .tb-date-btn .tb-day { font-size:10px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.05em; }
    .tb-date-btn .tb-num { font-size:18px;font-weight:900;color:#374151; }
    .tb-date-btn.active { background:#f97316;border-color:#f97316; }
    .tb-date-btn.active .tb-day, .tb-date-btn.active .tb-num { color:#fff; }
    .tb-time-btn { padding:9px 16px;background:#f9fafb;border:1.5px solid #e5e7eb;border-radius:10px;font-size:13px;font-weight:600;color:#374151;cursor:pointer;font-family:inherit;transition:all 0.15s; }
    .tb-time-btn.active, .tb-time-btn:hover { background:#f97316;border-color:#f97316;color:#fff; }
    #tb-next:not([disabled]) { opacity:1;cursor:pointer; }
    @keyframes tb-spin { to { transform:rotate(360deg); } }
  </style>`;
}

// ─── Main HTML Builder ─────────────────────────────────────────────────────────
export function generateTemplateHTML(
  business: NormalizedBusiness,
  content?: GeneratedContent
): string {
  const theme = getTheme(business.service_type);

  // Content with fallbacks
  const services = content?.services?.length
    ? content.services.map(s => ({ name: s.name, description: s.description }))
    : getDefaultServices(business.service_type);

  // Strip any emojis from content that AI may have generated
  const stripEmoji = (str: string) =>
    str.replace(/(\p{Emoji_Presentation}|\p{Extended_Pictographic})\s*/gu, "").trim();

  const hero         = stripEmoji(content?.hero         || `${business.name} — Trusted ${business.service_type} in ${business.city}`);
  const subheadline  = stripEmoji(content?.subheadline  || `Serving ${business.city}${business.state ? `, ${business.state}` : ""} with expert work, honest pricing, and a guarantee you can count on.`);
  const cta          = stripEmoji(content?.cta          || "Get Your Free Estimate");
  const aboutSnippet = stripEmoji(content?.about_snippet || `We are a locally owned ${business.service_type.toLowerCase()} company proudly serving ${business.city} and the surrounding area. Our team brings experience, integrity, and a commitment to doing the job right every single time. When you call us, you are calling your neighbors.`);

  const trustSignals = (content?.trust_signals ?? [
    "Licensed & Insured",
    "5-Star Rated",
    "Same-Day Service Available",
    `Serving ${business.city}`,
  ]).map(stripEmoji);

  const phone        = business.phone || "(555) 000-0000";
  const phoneClean   = phone.replace(/\D/g, "");
  const yearsText    = business.years_in_business ? `${business.years_in_business} Years` : "Family Owned";
  const reviewCount  = business.review_count      ? `${business.review_count}+`           : "100+";

  const p  = theme.primary;
  const pd = theme.primaryDark;

  // Build service cards HTML
  const servicesHtml = services.map(s => {
    const icon = svgIcon(iconForService(s.name), p);
    return `
      <div class="svc-card">
        <div class="svc-icon">${icon}</div>
        <h3 class="svc-name">${s.name}</h3>
        <p class="svc-desc">${stripEmoji(s.description)}</p>
      </div>`;
  }).join("");

  // Trust bar items
  const trustHtml = trustSignals.map(t => `
    <div class="trust-item">
      <svg class="trust-check" viewBox="0 0 24 24" fill="none" stroke="${p}" stroke-width="2.5">
        <polyline points="20 6 9 17 4 12" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span>${t}</span>
    </div>`).join("");

  // Testimonials
  const reviewsHtml = TESTIMONIALS.map(t => `
    <div class="review-card">
      <div class="review-stars">
        ${Array(t.stars).fill(`<svg viewBox="0 0 24 24" fill="${p}" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`).join("")}
      </div>
      <p class="review-text">${t.text}</p>
      <p class="review-author">— ${t.name}</p>
    </div>`).join("");

  // Process steps
  const processSteps = [
    { n: "01", title: "Call or Request Online", desc: `Reach us by phone or submit your info. We respond same day.` },
    { n: "02", title: "Get a Written Estimate", desc: `We assess the work and give you a clear, itemized quote — no guessing.` },
    { n: "03", title: "Work Done Right",         desc: `Our team completes the job cleanly and thoroughly. You inspect, we guarantee it.` },
  ];
  const processHtml = processSteps.map(s => `
    <div class="step">
      <div class="step-num" style="background:${p}">${s.n}</div>
      <h3 class="step-title">${s.title}</h3>
      <p class="step-desc">${s.desc}</p>
    </div>`).join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${business.name} — ${business.service_type} in ${business.city}</title>
  <meta name="description" content="${subheadline}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html  { scroll-behavior: smooth; font-size: 16px; }
    body  { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #fff; color: #111827; line-height: 1.6; -webkit-font-smoothing: antialiased; }

    /* ── NAV ───────────────────────────────────────────────────────── */
    .nav {
      position: fixed; top: 0; left: 0; right: 0; z-index: 100;
      display: flex; align-items: center; justify-content: space-between;
      padding: 0 2rem; height: 68px;
      background: rgba(255,255,255,0.92);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-bottom: 1px solid rgba(0,0,0,0.07);
    }
    .nav-logo { font-weight: 800; font-size: 1.05rem; color: #111827; text-decoration: none; letter-spacing: -0.03em; }
    .nav-phone { font-weight: 600; font-size: 0.95rem; color: #374151; text-decoration: none; }
    .nav-cta {
      background: ${p}; color: #fff;
      padding: 0.6rem 1.4rem; border-radius: 8px;
      font-weight: 700; font-size: 0.9rem;
      text-decoration: none; border: none; cursor: pointer;
      transition: background 0.15s, transform 0.15s;
    }
    .nav-cta:hover { background: ${pd}; transform: translateY(-1px); }

    /* ── HERO ──────────────────────────────────────────────────────── */
    .hero {
      min-height: 100vh;
      background: ${theme.gradient};
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      text-align: center; padding: 7rem 1.5rem 5rem;
      position: relative; overflow: hidden;
    }
    .hero::before {
      content: ''; position: absolute; inset: 0;
      background: radial-gradient(ellipse 90% 70% at 50% -10%, rgba(255,255,255,0.06), transparent);
      pointer-events: none;
    }
    /* Dot grid overlay */
    .hero::after {
      content: ''; position: absolute; inset: 0;
      background-image: radial-gradient(rgba(255,255,255,0.07) 1px, transparent 1px);
      background-size: 28px 28px; pointer-events: none;
    }
    .hero-inner { position: relative; z-index: 1; max-width: 820px; }
    .hero-badge {
      display: inline-flex; align-items: center; gap: 0.5rem;
      background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);
      color: rgba(255,255,255,0.85);
      font-size: 0.78rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
      padding: 0.45rem 1rem; border-radius: 100px; margin-bottom: 2rem;
      animation: fadeUp 0.6s ease both;
    }
    .hero-badge-dot { width: 6px; height: 6px; border-radius: 50%; background: ${p}; flex-shrink: 0; }
    .hero h1 {
      font-size: clamp(2.4rem, 6vw, 4.2rem);
      font-weight: 900; letter-spacing: -0.04em; line-height: 1.05; color: #fff;
      margin-bottom: 1.25rem;
      animation: fadeUp 0.7s ease 0.1s both;
    }
    .hero-sub {
      font-size: clamp(1rem, 2vw, 1.2rem); color: rgba(255,255,255,0.72);
      max-width: 560px; margin: 0 auto 2.5rem;
      animation: fadeUp 0.7s ease 0.2s both;
    }
    .hero-actions {
      display: flex; flex-wrap: wrap; gap: 1rem; justify-content: center;
      animation: fadeUp 0.7s ease 0.3s both;
    }
    .btn-primary {
      display: inline-flex; align-items: center; gap: 0.6rem;
      background: ${p}; color: #fff;
      padding: 0.95rem 2.2rem; border-radius: 10px;
      font-weight: 800; font-size: 1rem; letter-spacing: -0.01em;
      text-decoration: none; border: none; cursor: pointer;
      transition: background 0.15s, transform 0.15s, box-shadow 0.15s;
      box-shadow: 0 4px 24px rgba(0,0,0,0.25);
    }
    .btn-primary:hover { background: ${pd}; transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
    .btn-ghost {
      display: inline-flex; align-items: center; gap: 0.6rem;
      background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.22);
      color: #fff; padding: 0.95rem 2.2rem; border-radius: 10px;
      font-weight: 600; font-size: 1rem;
      text-decoration: none; cursor: pointer;
      transition: background 0.15s;
    }
    .btn-ghost:hover { background: rgba(255,255,255,0.18); }
    .hero-note { margin-top: 1.5rem; font-size: 0.8rem; color: rgba(255,255,255,0.45); animation: fadeUp 0.6s ease 0.45s both; }

    /* ── TRUST BAR ─────────────────────────────────────────────────── */
    .trust-bar {
      background: #fff; border-bottom: 1px solid #f0ece6;
      padding: 1.1rem 2rem;
      display: flex; flex-wrap: wrap; justify-content: center; gap: 1.75rem;
    }
    .trust-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; font-weight: 600; color: #374151; }
    .trust-check { width: 18px; height: 18px; flex-shrink: 0; }

    /* ── SHARED SECTION STYLES ─────────────────────────────────────── */
    .section { padding: 5.5rem 1.5rem; }
    .section-inner { max-width: 1100px; margin: 0 auto; }
    .section-label { text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.72rem; font-weight: 700; color: ${p}; margin-bottom: 0.6rem; }
    .section-title { font-size: clamp(1.8rem, 4vw, 2.8rem); font-weight: 900; letter-spacing: -0.04em; line-height: 1.1; color: #111827; margin-bottom: 1rem; }
    .section-sub { font-size: 1.05rem; color: #6b7280; max-width: 540px; line-height: 1.65; }

    /* ── SERVICES ──────────────────────────────────────────────────── */
    .services-bg { background: #fdf8f2; }
    .services-header { max-width: 540px; margin-bottom: 3.5rem; }
    .services-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 1.25rem;
    }
    .svc-card {
      background: #fff; border: 1px solid rgba(0,0,0,0.07);
      border-radius: 16px; padding: 2rem 1.75rem;
      transition: box-shadow 0.2s, transform 0.2s;
    }
    .svc-card:hover { box-shadow: 0 8px 32px rgba(0,0,0,0.09); transform: translateY(-3px); }
    .svc-icon { width: 48px; height: 48px; background: ${theme.badgeBg}; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 1.1rem; padding: 11px; }
    .svc-icon svg { width: 100%; height: 100%; }
    .svc-name { font-size: 1rem; font-weight: 700; color: #111827; margin-bottom: 0.5rem; letter-spacing: -0.02em; }
    .svc-desc { font-size: 0.9rem; color: #6b7280; line-height: 1.65; }

    /* ── ABOUT ─────────────────────────────────────────────────────── */
    .about-bg { background: ${theme.bg}; }
    .about-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 4rem; align-items: center; }
    .about-label { color: ${p}; }
    .about-title { color: #fff; }
    .about-body { color: rgba(255,255,255,0.72); font-size: 1.05rem; line-height: 1.8; margin-top: 1rem; }
    .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .stat-card { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 1.75rem; text-align: center; }
    .stat-number { display: block; font-size: 2.4rem; font-weight: 900; color: ${p}; letter-spacing: -0.04em; line-height: 1; margin-bottom: 0.4rem; }
    .stat-label { font-size: 0.82rem; color: rgba(255,255,255,0.55); font-weight: 500; }

    /* ── PROCESS ───────────────────────────────────────────────────── */
    .process-bg { background: #fff; border-top: 1px solid #f0ece6; border-bottom: 1px solid #f0ece6; }
    .steps-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 2rem; margin-top: 3rem; }
    .step { text-align: center; }
    .step-num { display: inline-flex; align-items: center; justify-content: center; width: 48px; height: 48px; border-radius: 12px; color: #fff; font-weight: 900; font-size: 0.85rem; letter-spacing: 0.05em; margin: 0 auto 1.25rem; }
    .step-title { font-size: 1rem; font-weight: 700; color: #111827; margin-bottom: 0.5rem; letter-spacing: -0.02em; }
    .step-desc { font-size: 0.9rem; color: #6b7280; line-height: 1.65; }

    /* ── REVIEWS ───────────────────────────────────────────────────── */
    .reviews-bg { background: #fdf8f2; }
    .reviews-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.25rem; margin-top: 3.5rem; }
    .review-card { background: #fff; border: 1px solid rgba(0,0,0,0.07); border-radius: 16px; padding: 2rem 1.75rem; }
    .review-stars { display: flex; gap: 3px; margin-bottom: 1rem; }
    .review-stars svg { width: 16px; height: 16px; }
    .review-text { font-size: 0.95rem; color: #374151; line-height: 1.75; font-style: italic; margin-bottom: 1.1rem; }
    .review-author { font-size: 0.85rem; font-weight: 600; color: #6b7280; }

    /* ── FINAL CTA ─────────────────────────────────────────────────── */
    .cta-bg {
      background: ${theme.gradient}; padding: 6rem 1.5rem;
      text-align: center; position: relative; overflow: hidden;
    }
    .cta-bg::after {
      content: ''; position: absolute; inset: 0;
      background-image: radial-gradient(rgba(255,255,255,0.06) 1px, transparent 1px);
      background-size: 28px 28px; pointer-events: none;
    }
    .cta-inner { position: relative; z-index: 1; max-width: 640px; margin: 0 auto; }
    .cta-title { font-size: clamp(2rem, 5vw, 3.2rem); font-weight: 900; color: #fff; letter-spacing: -0.04em; line-height: 1.08; margin-bottom: 1rem; }
    .cta-sub { font-size: 1.1rem; color: rgba(255,255,255,0.7); margin-bottom: 2.5rem; }
    .cta-phone { display: block; font-size: clamp(2rem, 5vw, 3rem); font-weight: 900; color: #fff; text-decoration: none; letter-spacing: -0.04em; margin-bottom: 2rem; transition: opacity 0.15s; }
    .cta-phone:hover { opacity: 0.85; }
    .cta-note { margin-top: 1.5rem; font-size: 0.8rem; color: rgba(255,255,255,0.4); }

    /* ── FOOTER ────────────────────────────────────────────────────── */
    .footer { background: #0f172a; padding: 2.5rem 2rem; }
    .footer-inner { max-width: 1100px; margin: 0 auto; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 1rem; }
    .footer-logo { font-weight: 800; font-size: 1rem; color: #f8fafc; letter-spacing: -0.03em; }
    .footer-info { font-size: 0.85rem; color: #94a3b8; }
    .footer-copy { font-size: 0.8rem; color: #475569; }

    /* ── ANIMATIONS ────────────────────────────────────────────────── */
    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(20px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .fade-in { opacity: 0; transform: translateY(20px); transition: opacity 0.55s ease, transform 0.55s ease; }
    .fade-in.visible { opacity: 1; transform: none; }

    /* ── RESPONSIVE ────────────────────────────────────────────────── */
    @media (max-width: 768px) {
      .nav-phone { display: none; }
      .about-grid { grid-template-columns: 1fr; gap: 2.5rem; }
      .stats-grid { grid-template-columns: 1fr 1fr; }
      .section { padding: 4rem 1.25rem; }
    }
  </style>
</head>
<body>

  <!-- NAV -->
  <nav class="nav">
    <a class="nav-logo" href="#">${business.name}</a>
    <a class="nav-phone" href="tel:${phoneClean}">${phone}</a>
    <a class="btn-cta nav-cta" href="tel:${phoneClean}">${cta}</a>
  </nav>

  <!-- HERO -->
  <section class="hero">
    <div class="hero-inner">
      <div class="hero-badge">
        <span class="hero-badge-dot"></span>
        ${business.service_type} · ${business.city}${business.state ? `, ${business.state}` : ""}
      </div>
      <h1>${hero}</h1>
      <p class="hero-sub">${subheadline}</p>
      <div class="hero-actions">
        <a class="btn-primary" href="tel:${phoneClean}">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">${ICONS.phone}</svg>
          Call ${phone}
        </a>
        <a class="btn-ghost" href="#services">See Services</a>
      </div>
      <p class="hero-note">Licensed & Insured &nbsp;·&nbsp; Free Estimates &nbsp;·&nbsp; Serving ${business.city}</p>
    </div>
  </section>

  <!-- TRUST BAR -->
  <div class="trust-bar">${trustHtml}</div>

  <!-- SERVICES -->
  <section id="services" class="section services-bg">
    <div class="section-inner">
      <div class="services-header fade-in">
        <p class="section-label">What We Do</p>
        <h2 class="section-title">Services built for ${business.city} homeowners</h2>
        <p class="section-sub">Every job handled in-house by our own team — no subcontractors, no shortcuts.</p>
      </div>
      <div class="services-grid">${servicesHtml}</div>
    </div>
  </section>

  <!-- ABOUT -->
  <section class="section about-bg">
    <div class="section-inner">
      <div class="about-grid">
        <div class="about-text fade-in">
          <p class="section-label about-label">About Us</p>
          <h2 class="section-title about-title">Local. Experienced. Accountable.</h2>
          <p class="about-body">${aboutSnippet}</p>
          <a class="btn-primary" href="tel:${phoneClean}" style="margin-top:2rem;display:inline-flex;">Call Us Today</a>
        </div>
        <div class="stats-grid fade-in">
          <div class="stat-card">
            <span class="stat-number">${reviewCount}</span>
            <span class="stat-label">5-Star Reviews</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">${yearsText}</span>
            <span class="stat-label">In Business</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">24/7</span>
            <span class="stat-label">Emergency Line</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">Free</span>
            <span class="stat-label">Estimates</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- PROCESS -->
  <section class="section process-bg">
    <div class="section-inner">
      <div class="fade-in" style="text-align:center;max-width:540px;margin:0 auto 1rem;">
        <p class="section-label">How It Works</p>
        <h2 class="section-title">Simple from the first call to the final walkthrough</h2>
      </div>
      <div class="steps-grid">${processHtml}</div>
    </div>
  </section>

  <!-- REVIEWS -->
  <section class="section reviews-bg">
    <div class="section-inner">
      <div class="fade-in">
        <p class="section-label">Reviews</p>
        <h2 class="section-title">What our customers say</h2>
        <p class="section-sub">Real reviews from homeowners in ${business.city} and the surrounding area.</p>
      </div>
      <div class="reviews-grid">${reviewsHtml}</div>
    </div>
  </section>

  ${business._bookingBusinessId ? bookingWidgetHtml(business, content) : ""}

  <!-- FINAL CTA -->
  <section class="cta-bg">
    <div class="cta-inner">
      <h2 class="cta-title">Ready to get the job done right?</h2>
      <p class="cta-sub">Call now for a free estimate. We pick up the phone — no voicemail runaround.</p>
      <a class="cta-phone" href="tel:${phoneClean}">${phone}</a>
      <a class="btn-primary" href="tel:${phoneClean}" style="font-size:1.05rem;padding:1rem 2.5rem;">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">${ICONS.phone}</svg>
        Call for a Free Estimate
      </a>
      <p class="cta-note">Licensed & Insured &nbsp;·&nbsp; Serving ${business.city}${business.state ? `, ${business.state}` : ""}</p>
    </div>
  </section>

  <!-- FOOTER -->
  <footer class="footer">
    <div class="footer-inner">
      <span class="footer-logo">${business.name}</span>
      <span class="footer-info">${business.service_type} &nbsp;·&nbsp; ${business.city}${business.state ? `, ${business.state}` : ""} &nbsp;·&nbsp; <a href="tel:${phoneClean}" style="color:#94a3b8;text-decoration:none;">${phone}</a></span>
      <span class="footer-copy">Demo generated by TradeBuilt</span>
    </div>
  </footer>

  <script>
    // Scroll-triggered fade-in
    const obs = new IntersectionObserver(
      entries => entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); } }),
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );
    document.querySelectorAll('.fade-in').forEach(el => obs.observe(el));

    // ── Booking widget ──────────────────────────────────────────────────────────
    (function() {
      const API = document.getElementById('tb-booking-widget')?.dataset.api || '';
      const BIZ_ID = document.getElementById('tb-booking-widget')?.dataset.bid || '';
      if (!API || !BIZ_ID) return;

      let selectedSlot = null;
      let slotsData = {};
      let selectedDate = null;

      const modal   = document.getElementById('tb-modal');
      const fab     = document.getElementById('tb-fab');
      const loading = document.getElementById('tb-loading');
      const picker  = document.getElementById('tb-picker');
      const form    = document.getElementById('tb-form');
      const confirm = document.getElementById('tb-confirm');
      const dateRow = document.getElementById('tb-dates');
      const timeRow = document.getElementById('tb-times');
      const noSlots = document.getElementById('tb-no-slots');

      if (!modal) return;

      fab.addEventListener('click', () => openModal());
      document.getElementById('tb-close').addEventListener('click', () => closeModal());
      modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

      async function openModal() {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        showScreen('loading');
        try {
          const res  = await fetch(API + '/api/booking/slots?business_id=' + BIZ_ID + '&days=7');
          const json = await res.json();
          slotsData  = json.slots || {};
          buildDatePicker();
          showScreen('picker');
        } catch(e) {
          showScreen('picker');
          noSlots.style.display = 'block';
          dateRow.style.display = 'none';
          timeRow.style.display = 'none';
        }
      }

      function closeModal() {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        showScreen('picker');
        selectedSlot = null;
        selectedDate = null;
      }

      function showScreen(s) {
        loading.style.display = s === 'loading' ? 'flex' : 'none';
        picker.style.display  = s === 'picker'  ? 'block' : 'none';
        form.style.display    = s === 'form'    ? 'block' : 'none';
        confirm.style.display = s === 'confirm' ? 'block' : 'none';
      }

      function buildDatePicker() {
        const dates = Object.keys(slotsData);
        if (dates.length === 0) {
          noSlots.style.display = 'block';
          dateRow.style.display = 'none';
          timeRow.style.display = 'none';
          return;
        }
        noSlots.style.display = 'none';
        dateRow.innerHTML = '';
        dates.forEach((d, i) => {
          const dt   = new Date(d + 'T12:00:00');
          const btn  = document.createElement('button');
          btn.className = 'tb-date-btn' + (i === 0 ? ' active' : '');
          btn.innerHTML = '<span class="tb-day">' + dt.toLocaleDateString('en-US',{weekday:'short'}) + '</span><span class="tb-num">' + dt.getDate() + '</span>';
          btn.addEventListener('click', () => selectDate(d, btn));
          dateRow.appendChild(btn);
        });
        selectDate(dates[0], dateRow.firstChild);
      }

      function selectDate(date, btn) {
        selectedDate = date;
        selectedSlot = null;
        dateRow.querySelectorAll('.tb-date-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        buildTimeSlots(date);
      }

      function buildTimeSlots(date) {
        const slots = (slotsData[date] || []).filter(s => s.available);
        timeRow.innerHTML = '';
        if (slots.length === 0) {
          timeRow.innerHTML = '<p style="color:#6b7280;font-size:13px;margin:0;">No slots available — try another day.</p>';
          return;
        }
        slots.forEach(slot => {
          const btn = document.createElement('button');
          btn.className = 'tb-time-btn';
          btn.textContent = slot.label;
          btn.dataset.iso = slot.start;
          btn.addEventListener('click', () => {
            timeRow.querySelectorAll('.tb-time-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedSlot = slot;
            document.getElementById('tb-next').disabled = false;
          });
          timeRow.appendChild(btn);
        });
        document.getElementById('tb-next').disabled = true;
      }

      document.getElementById('tb-next').addEventListener('click', () => {
        if (!selectedSlot) return;
        const dt = new Date(selectedSlot.start);
        document.getElementById('tb-slot-label').textContent =
          dt.toLocaleDateString('en-US',{weekday:'long',month:'short',day:'numeric'}) + ' at ' + selectedSlot.label;
        showScreen('form');
      });

      document.getElementById('tb-back').addEventListener('click', () => showScreen('picker'));

      document.getElementById('tb-booking-form').addEventListener('submit', async e => {
        e.preventDefault();
        if (!selectedSlot) return;
        const name    = document.getElementById('tb-name').value.trim();
        const phone   = document.getElementById('tb-phone').value.trim();
        const service = document.getElementById('tb-service')?.value || '';
        const submit  = document.getElementById('tb-submit');
        submit.disabled = true;
        submit.textContent = 'Booking…';
        try {
          const res = await fetch(API + '/api/booking/book', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              business_id: BIZ_ID,
              customer_name: name,
              customer_phone: phone,
              service: service || undefined,
              start_time: selectedSlot.start,
            }),
          });
          if (!res.ok) throw new Error((await res.json()).error || 'Booking failed');
          const dt = new Date(selectedSlot.start);
          document.getElementById('tb-confirm-name').textContent = name;
          document.getElementById('tb-confirm-time').textContent =
            dt.toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'}) + ' at ' + selectedSlot.label;
          showScreen('confirm');
        } catch(err) {
          alert(err.message || 'Booking failed. Please try again.');
          submit.disabled = false;
          submit.textContent = 'Confirm Booking';
        }
      });

      document.getElementById('tb-done').addEventListener('click', closeModal);
    })();
  </script>
</body>
</html>`;
}
