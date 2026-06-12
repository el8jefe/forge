"use client";

import Link from "next/link";
import { motion, useScroll, useTransform } from "framer-motion";
import { PageWrapper, Reveal, StaggerGroup, StaggerItem, ease } from "@/components/ui/motion";
import { TBIcon } from "@/components/ui/logo";
import { LIGHT, DARK, ThemeProvider, useT, useTheme, ThemeToggle } from "@/lib/theme";

// ── Feature icons (SVG line icons, 20×20, stroke style) ───────────────────────
function IconZap() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M11.5 2L4 11h6.5l-2 7L17 9h-6.5l1-7z" stroke="#f97316" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
function IconTarget() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="7.5" stroke="#f97316" strokeWidth="1.5"/>
      <circle cx="10" cy="10" r="4" stroke="#f97316" strokeWidth="1.5"/>
      <circle cx="10" cy="10" r="1.25" fill="#f97316"/>
    </svg>
  );
}
function IconCpu() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <rect x="5.5" y="5.5" width="9" height="9" rx="1.5" stroke="#f97316" strokeWidth="1.5"/>
      <rect x="8" y="8" width="4" height="4" rx="0.5" fill="#f97316"/>
      <path d="M8 5.5V3M10 5.5V3M12 5.5V3M8 14.5V17M10 14.5V17M12 14.5V17M5.5 8H3M5.5 10H3M5.5 12H3M14.5 8H17M14.5 10H17M14.5 12H17" stroke="#f97316" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}
function IconPipeline() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <rect x="2" y="4" width="4.5" height="12" rx="1" stroke="#f97316" strokeWidth="1.5"/>
      <rect x="7.75" y="4" width="4.5" height="8" rx="1" stroke="#f97316" strokeWidth="1.5"/>
      <rect x="13.5" y="4" width="4.5" height="5" rx="1" stroke="#f97316" strokeWidth="1.5"/>
    </svg>
  );
}
function IconSend() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M17.5 2.5L2 8.5l6.5 3L17.5 2.5z" stroke="#f97316" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M8.5 11.5L17.5 2.5" stroke="#f97316" strokeWidth="1.5" strokeLinecap="round"/>
      <path d="M8.5 11.5v6l3.5-3.5" stroke="#f97316" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
function IconWrench() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M14.5 3.5a3.5 3.5 0 00-3.46 4.04L4.5 14.5a1.5 1.5 0 002.12 2.12l6.96-6.54A3.5 3.5 0 1014.5 3.5z" stroke="#f97316" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="5.5" cy="15.5" r="0.75" fill="#f97316"/>
    </svg>
  );
}

// ── Data ──────────────────────────────────────────────────────────────────────
const FEATURES = [
  {
    number: "01",
    title: "Demo site in seconds",
    description:
      "Type any trade business name and city. TradeBuilt returns a complete, mobile-ready website with professional copy, custom colors, and a layout built to convert.",
    icon: <IconZap />,
  },
  {
    number: "02",
    title: "Dual-layer lead scoring",
    description:
      "Every business gets two scores: website quality and lead value. Burning Hot leads have no website, real reviews, and full contact info. You know before you call.",
    icon: <IconTarget />,
  },
  {
    number: "03",
    title: "AI-written copy",
    description:
      "Claude AI writes headlines, service descriptions, and CTAs specific to the trade, city, and business name. Not templates. Not fill-in-the-blank.",
    icon: <IconCpu />,
  },
  {
    number: "04",
    title: "Built-in CRM pipeline",
    description:
      "Track every lead from first touch to closed deal. Mark contacted, emailed, called, won — in a clean pipeline without a third-party tool.",
    icon: <IconPipeline />,
  },
  {
    number: "05",
    title: "One-click outreach",
    description:
      "Send a human-written cold email with the demo link directly from the pipeline. No copy-paste. No mail merge. No friction.",
    icon: <IconSend />,
  },
  {
    number: "06",
    title: "Trade-specific design",
    description:
      "HVAC, plumbing, electrical, roofing — each trade gets a custom color palette, typography, and layout that signals professionalism on sight.",
    icon: <IconWrench />,
  },
];

const TRADES = ["HVAC", "Plumbing", "Electrical", "Roofing", "Landscaping", "Painting", "Pest Control", "Cleaning", "Concrete", "Solar"];

const STATS = [
  { value: "10+", label: "Trade verticals" },
  { value: "< 5s", label: "Demo generation" },
  { value: "100%", label: "Mobile ready" },
  { value: "2-layer", label: "Lead scoring" },
];

const PRICING = [
  {
    tier: "Free",
    price: "$0",
    period: "",
    description: "Start generating demos today — no card needed.",
    cta: "Start free",
    href: "/generate",
    features: [
      "10 template sites per month",
      "Website quality scoring",
      "Download HTML demos",
      "Save leads to pipeline",
      "Lead temperature rating",
    ],
    accent: false,
  },
  {
    tier: "Pro",
    price: "$49",
    period: "/mo",
    description: "Everything you need to close trade clients at scale.",
    cta: "Get Pro",
    href: "/billing",
    features: [
      "Everything in Free",
      "Unlimited AI generation",
      "Full dual-layer scoring",
      "1-click email outreach",
      "Complete CRM pipeline",
      "Priority support",
    ],
    accent: true,
  },
];

const INTEGRATIONS = [
  // Core stack
  { name: "Claude AI",          color: "#D97706", bg: "rgba(217,119,6,0.08)",    letter: "A",  tag: "AI engine" },
  { name: "Supabase",           color: "#3ECF8E", bg: "rgba(62,207,142,0.08)",   letter: "S",  tag: "Database" },
  { name: "Stripe",             color: "#635BFF", bg: "rgba(99,91,255,0.08)",    letter: "$",  tag: "Payments" },
  { name: "Firecrawl",          color: "#EF4444", bg: "rgba(239,68,68,0.08)",    letter: "F",  tag: "Scraping" },
  { name: "Resend",             color: "#1C1208", bg: "rgba(28,18,8,0.07)",      letter: "R",  tag: "Email" },
  { name: "Twilio",             color: "#F22F46", bg: "rgba(242,47,70,0.08)",    letter: "T",  tag: "SMS" },
  { name: "Vercel",             color: "#000000", bg: "rgba(0,0,0,0.06)",        letter: "▲",  tag: "Deploy" },
  { name: "Cloudflare",         color: "#F48120", bg: "rgba(244,129,32,0.08)",   letter: "CF", tag: "CDN / Security" },
  // CRM & outreach
  { name: "HubSpot",            color: "#FF7A59", bg: "rgba(255,122,89,0.08)",   letter: "H",  tag: "CRM" },
  { name: "Salesforce",         color: "#00A1E0", bg: "rgba(0,161,224,0.08)",    letter: "SF", tag: "Enterprise CRM" },
  { name: "Pipedrive",          color: "#1A1F36", bg: "rgba(26,31,54,0.07)",     letter: "P",  tag: "Sales pipeline" },
  { name: "Apollo.io",          color: "#3B82F6", bg: "rgba(59,130,246,0.08)",   letter: "Ap", tag: "Lead intel" },
  { name: "GoHighLevel",        color: "#00BF63", bg: "rgba(0,191,99,0.08)",     letter: "G",  tag: "Agency OS" },
  // Outreach & email
  { name: "Mailchimp",          color: "#FFE01B", bg: "rgba(255,224,27,0.10)",   letter: "M",  tag: "Email marketing" },
  { name: "ActiveCampaign",     color: "#356AE6", bg: "rgba(53,106,230,0.08)",   letter: "AC", tag: "Automations" },
  { name: "Loom",               color: "#625DF5", bg: "rgba(98,93,245,0.08)",    letter: "Lo", tag: "Video outreach" },
  // Scheduling & contracts
  { name: "Calendly",           color: "#006BFF", bg: "rgba(0,107,255,0.08)",    letter: "Ca", tag: "Booking" },
  { name: "DocuSign",           color: "#FFCC00", bg: "rgba(255,204,0,0.10)",    letter: "D",  tag: "Contracts" },
  // Local biz data
  { name: "Google My Business", color: "#34A853", bg: "rgba(52,168,83,0.08)",    letter: "G+", tag: "Local listings" },
  { name: "Yelp",               color: "#D32323", bg: "rgba(211,35,35,0.08)",    letter: "Y",  tag: "Reviews" },
  // Workflow & automation
  { name: "Zapier",             color: "#FF4A00", bg: "rgba(255,74,0,0.08)",     letter: "Z",  tag: "Automation" },
  { name: "Make",               color: "#6D00CC", bg: "rgba(109,0,204,0.08)",    letter: "Mk", tag: "Workflows" },
  { name: "Webhooks",           color: "#6B7280", bg: "rgba(107,114,128,0.08)",  letter: "{}",  tag: "Custom triggers" },
  { name: "Airtable",           color: "#18BFFF", bg: "rgba(24,191,255,0.08)",   letter: "At", tag: "Client tracking" },
  // Comms & collab
  { name: "Slack",              color: "#4A154B", bg: "rgba(74,21,75,0.08)",     letter: "#",  tag: "Notifications" },
  { name: "Notion",             color: "#37352F", bg: "rgba(55,53,47,0.08)",     letter: "N",  tag: "Docs" },
  { name: "Linear",             color: "#5E6AD2", bg: "rgba(94,106,210,0.08)",   letter: "L",  tag: "Issues" },
  { name: "Google Calendar",    color: "#1A73E8", bg: "rgba(26,115,232,0.08)",   letter: "GC", tag: "Scheduling" },
  // Analytics
  { name: "PostHog",            color: "#F9A825", bg: "rgba(249,168,37,0.08)",   letter: "Ph", tag: "Analytics" },
  { name: "Segment",            color: "#52BD94", bg: "rgba(82,189,148,0.08)",   letter: "Sg", tag: "Data pipeline" },
];

const STEPS = [
  { n: "01", title: "Enter a business", desc: "Name and city. Any trade, any US city." },
  { n: "02", title: "Get a scored demo", desc: "Full website with lead temperature rating." },
  { n: "03", title: "Review the intel", desc: "See exactly why this lead is hot or cold." },
  { n: "04", title: "Send the pitch", desc: "One click. Real email. Demo link included." },
];

// Fallback alias (unused at runtime — each component calls useT())
const L = LIGHT;

// ── Components ─────────────────────────────────────────────────────────────────

function Nav() {
  const { t } = useTheme();
  return (
    <motion.nav
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: ease.smooth }}
      style={{
        position: "fixed", top: 0, left: 0, right: 0, zIndex: 50,
        borderBottom: `1px solid ${t.border}`,
        background: t.navBg,
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
      }}
    >
      <div style={{ maxWidth: 1152, margin: "0 auto", padding: "0 24px", height: 64, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <TBIcon size={22} />
          <span style={{ fontWeight: 900, fontSize: 17, letterSpacing: "-0.04em", color: t.text }}>TradeBuilt</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <Link href="/dashboard" style={{ fontSize: 14, fontWeight: 500, color: t.body, textDecoration: "none" }}>Dashboard</Link>
          <Link href="/auth/login" style={{ fontSize: 14, fontWeight: 500, color: t.body, textDecoration: "none" }}>Sign in</Link>
          <ThemeToggle />
          <Link href="/generate">
            <motion.span
              whileHover={{ scale: 1.03, boxShadow: t.orangeGlow }}
              whileTap={{ scale: 0.97 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
              style={{
                display: "inline-block", background: t.orange, color: "#fff",
                fontSize: 14, fontWeight: 700, padding: "9px 20px", borderRadius: 10,
                letterSpacing: "-0.01em",
              }}
            >
              Try free →
            </motion.span>
          </Link>
        </div>
      </div>
    </motion.nav>
  );
}

function Hero() {
  const t = useT();
  const { scrollY } = useScroll();
  const blob1Y = useTransform(scrollY, [0, 900], [0, -220]);
  const blob2Y = useTransform(scrollY, [0, 900], [0, 140]);
  const blob3Y = useTransform(scrollY, [0, 700], [0, -100]);
  const blob4Y = useTransform(scrollY, [0, 800], [0, 80]);
  const contentY = useTransform(scrollY, [0, 500], [0, -50]);

  return (
    <section className="line-pattern" style={{ position: "relative", minHeight: "100vh", display: "flex", alignItems: "center", overflow: "hidden" }}>
      {/* Mesh gradient blobs — all styles inline to avoid SSR/hydration mismatch */}
      {[
        { style: { y: blob1Y }, pos: { top: "-18%", right: "-8%" }, size: 1000, bg: "radial-gradient(circle, rgba(249,115,22,0.32) 0%, rgba(251,146,60,0.14) 45%, transparent 70%)" },
        { style: { y: blob2Y }, pos: { top: "20%", left: "-14%" },  size: 800,  bg: "radial-gradient(circle, rgba(251,191,36,0.22) 0%, rgba(249,115,22,0.08) 50%, transparent 70%)" },
        { style: { y: blob3Y }, pos: { bottom: "0%", right: "10%" },size: 700,  bg: "radial-gradient(circle, rgba(37,99,235,0.13) 0%, rgba(99,102,241,0.06) 50%, transparent 70%)" },
        { style: { y: blob4Y }, pos: { bottom: "10%", left: "20%" },size: 500,  bg: "radial-gradient(circle, rgba(249,115,22,0.10) 0%, transparent 65%)" },
      ].map((b, i) => (
        <motion.div key={i} style={{
          ...b.style, ...b.pos,
          position: "absolute", width: b.size, height: b.size,
          borderRadius: "50%", filter: "blur(80px)",
          background: b.bg, pointerEvents: "none", willChange: "transform",
        }} />
      ))}

      {/* Fade to next section */}
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: "35%", background: `linear-gradient(to bottom, transparent, ${t.heroFade})`, pointerEvents: "none" }} />

      <motion.div style={{ y: contentY, position: "relative", maxWidth: 980, margin: "0 auto", padding: "140px 24px 100px" }}>
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1, ease: ease.smooth }}
          style={{ marginBottom: 32 }}
        >
          <span style={{
            display: "inline-flex", alignItems: "center", gap: 8,
            background: "rgba(249,115,22,0.08)", border: "1px solid rgba(249,115,22,0.18)",
            color: t.orange, fontSize: 12, fontWeight: 700, letterSpacing: "0.06em",
            textTransform: "uppercase", padding: "6px 14px", borderRadius: 99,
          }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: t.orange, display: "block" }} />
            AI outreach for trade agencies
          </span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.18, ease: ease.smooth }}
          style={{ fontSize: "clamp(52px, 8vw, 88px)", fontWeight: 900, letterSpacing: "-0.04em", lineHeight: 1.0, color: t.text, marginBottom: 24 }}
        >
          Close trade clients
          <br />
          <span style={{
            background: "linear-gradient(135deg, #f97316 0%, #fb923c 55%, #fbbf24 100%)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text",
          }}>
            before lunch.
          </span>
        </motion.h1>

        {/* Sub */}
        <motion.p
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.28, ease: ease.smooth }}
          style={{ fontSize: 19, color: t.body, maxWidth: 560, lineHeight: 1.65, marginBottom: 40, fontWeight: 400 }}
        >
          Enter any local trade business. Get a full scored demo site, a lead temperature rating,
          and a one-click cold email — in under 5 seconds.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.38, ease: ease.smooth }}
          style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center" }}
        >
          <Link href="/generate">
            <motion.span
              whileHover={{ scale: 1.03, boxShadow: t.orangeGlow }}
              whileTap={{ scale: 0.97 }}
              transition={{ type: "spring", stiffness: 380, damping: 26 }}
              style={{
                display: "inline-flex", alignItems: "center", gap: 8,
                background: t.orange, color: "#fff", fontWeight: 800, fontSize: 16,
                padding: "14px 28px", borderRadius: 12, letterSpacing: "-0.02em", cursor: "pointer",
                boxShadow: "0 4px 20px rgba(249,115,22,0.22)",
              }}
            >
              Generate a demo site
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </motion.span>
          </Link>
          <Link href="/dashboard">
            <motion.span
              whileHover={{ scale: 1.02, boxShadow: t.shadowHover }}
              whileTap={{ scale: 0.97 }}
              transition={{ type: "spring", stiffness: 380, damping: 26 }}
              style={{
                display: "inline-flex", alignItems: "center", gap: 8,
                background: t.card, border: `1px solid ${t.border}`, boxShadow: t.shadow,
                color: t.text, fontWeight: 600, fontSize: 16,
                padding: "14px 28px", borderRadius: 12, letterSpacing: "-0.02em", cursor: "pointer",
              }}
            >
              View pipeline
            </motion.span>
          </Link>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}
          style={{ fontSize: 13, color: t.muted, marginTop: 20 }}
        >
          No account required · Free to start · 5-second results
        </motion.p>
      </motion.div>
    </section>
  );
}

function StatsBar() {
  const t = useT();
  return (
    <Reveal>
      <div style={{ borderTop: `1px solid ${t.border}`, borderBottom: `1px solid ${t.border}`, background: t.card, padding: "28px 24px" }}>
        <div style={{ maxWidth: 900, margin: "0 auto", display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
          {STATS.map((s) => (
            <div key={s.label} style={{ textAlign: "center" }}>
              <div style={{ fontSize: 28, fontWeight: 900, color: t.orange, letterSpacing: "-0.04em" }}>{s.value}</div>
              <div style={{ fontSize: 11, color: t.muted, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", marginTop: 3 }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </Reveal>
  );
}

function TradesRow() {
  const t = useT();
  return (
    <Reveal>
      <div style={{ padding: "44px 24px", background: t.bg2 }}>
        <div style={{ maxWidth: 900, margin: "0 auto" }}>
          <p style={{ textAlign: "center", fontSize: 11, fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase", color: t.muted, marginBottom: 20 }}>
            Works for every trade
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 8 }}>
            {TRADES.map((trade) => (
              <span key={trade} style={{
                background: t.card, border: `1px solid ${t.border}`, boxShadow: t.shadow,
                color: t.body, fontSize: 13, fontWeight: 500, padding: "7px 16px", borderRadius: 99,
              }}>
                {trade}
              </span>
            ))}
          </div>
        </div>
      </div>
    </Reveal>
  );
}

function Features() {
  const t = useT();
  return (
    <section style={{ padding: "100px 24px", background: t.bg }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <Reveal>
          <div style={{ maxWidth: 560, marginBottom: 60 }}>
            <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.14em", textTransform: "uppercase", color: t.orange, marginBottom: 12 }}>
              Why TradeBuilt
            </p>
            <h2 style={{ fontSize: "clamp(36px, 5vw, 52px)", fontWeight: 900, color: t.text, lineHeight: 1.05, letterSpacing: "-0.04em", marginBottom: 16 }}>
              The complete outreach stack —{" "}
              <span style={{ color: t.muted }}>in one tool</span>
            </h2>
            <p style={{ color: t.body, fontSize: 17, lineHeight: 1.6 }}>
              From demo generation to a closed client, without switching tools or wasting time.
            </p>
          </div>
        </Reveal>

        <StaggerGroup style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 16 }}>
          {FEATURES.map((f) => (
            <StaggerItem key={f.number}>
              <motion.div
                whileHover={{ y: -4, boxShadow: t.shadowHover }}
                transition={{ type: "spring", stiffness: 300, damping: 24 }}
                style={{
                  background: t.card, border: `1px solid ${t.border}`, boxShadow: t.shadow,
                  borderRadius: 16, padding: "28px 24px", height: "100%", boxSizing: "border-box",
                }}
              >
                <div style={{ fontSize: 11, fontWeight: 900, color: t.muted, letterSpacing: "0.12em", marginBottom: 16 }}>{f.number}</div>
                <div style={{ fontSize: 22, marginBottom: 12 }}>{f.icon}</div>
                <h3 style={{ fontWeight: 700, color: t.text, fontSize: 15, marginBottom: 10, letterSpacing: "-0.02em" }}>{f.title}</h3>
                <p style={{ color: t.body, fontSize: 14, lineHeight: 1.65 }}>{f.description}</p>
              </motion.div>
            </StaggerItem>
          ))}
        </StaggerGroup>
      </div>
    </section>
  );
}

function Process() {
  const t = useT();
  return (
    <section className="cross-grid" style={{ padding: "100px 24px", borderTop: `1px solid ${t.border}`, borderBottom: `1px solid ${t.border}` }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <Reveal>
          <div style={{ textAlign: "center", marginBottom: 64 }}>
            <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.14em", textTransform: "uppercase", color: t.orange, marginBottom: 12 }}>
              How it works
            </p>
            <h2 style={{ fontSize: "clamp(36px, 5vw, 52px)", fontWeight: 900, color: t.text, letterSpacing: "-0.04em", lineHeight: 1.05 }}>
              Zero to sent pitch
              <br />
              <span style={{
                background: "linear-gradient(135deg, #2563eb 0%, #f97316 100%)",
                WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text",
              }}>
                in under 60 seconds
              </span>
            </h2>
          </div>
        </Reveal>

        <StaggerGroup style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 16 }}>
          {STEPS.map((s) => (
            <StaggerItem key={s.n}>
              <div style={{ background: t.card, border: `1px solid ${t.border}`, boxShadow: t.shadow, borderRadius: 16, padding: 24 }}>
                <div style={{
                  display: "inline-flex", alignItems: "center", justifyContent: "center",
                  width: 40, height: 40, borderRadius: 10,
                  background: "linear-gradient(135deg, #f97316, #ea6c0a)",
                  color: "#fff", fontSize: 12, fontWeight: 900, letterSpacing: "0.05em",
                  marginBottom: 16, boxShadow: "0 4px 16px rgba(249,115,22,0.25)",
                }}>
                  {s.n}
                </div>
                <h3 style={{ fontWeight: 700, color: t.text, fontSize: 14, marginBottom: 8, letterSpacing: "-0.02em" }}>{s.title}</h3>
                <p style={{ color: t.body, fontSize: 13, lineHeight: 1.6 }}>{s.desc}</p>
              </div>
            </StaggerItem>
          ))}
        </StaggerGroup>
      </div>
    </section>
  );
}

function Pricing() {
  const t = useT();
  return (
    <section style={{ padding: "100px 24px", background: t.bg }}>
      <div style={{ maxWidth: 820, margin: "0 auto" }}>
        <Reveal>
          <div style={{ textAlign: "center", marginBottom: 64 }}>
            <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.14em", textTransform: "uppercase", color: t.orange, marginBottom: 12 }}>
              Pricing
            </p>
            <h2 style={{ fontSize: "clamp(36px, 5vw, 52px)", fontWeight: 900, color: t.text, letterSpacing: "-0.04em", marginBottom: 12 }}>
              Simple. No bullshit.
            </h2>
            <p style={{ color: t.body, fontSize: 17 }}>
              Start free. Upgrade when you land your first client.
            </p>
          </div>
        </Reveal>

        <StaggerGroup style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 20 }}>
          {PRICING.map((plan) => (
            <StaggerItem key={plan.tier}>
              <motion.div
                whileHover={{ y: -4, boxShadow: plan.accent ? "0 12px 40px rgba(249,115,22,0.18), 0 4px 16px rgba(0,0,0,0.08)" : t.shadowHover }}
                transition={{ type: "spring", stiffness: 300, damping: 24 }}
                style={{
                  position: "relative", borderRadius: 22, padding: 32,
                  height: "100%", boxSizing: "border-box", display: "flex", flexDirection: "column",
                  ...(plan.accent ? {
                    background: t.card,
                    border: "1.5px solid rgba(249,115,22,0.35)",
                    boxShadow: "0 8px 32px rgba(249,115,22,0.12), 0 2px 8px rgba(0,0,0,0.06)",
                  } : {
                    background: t.card,
                    border: `1px solid ${t.border}`,
                    boxShadow: t.shadow,
                  }),
                }}
              >
                {plan.accent && (
                  <div style={{
                    position: "absolute", top: -13, left: "50%", transform: "translateX(-50%)",
                    background: "linear-gradient(90deg, #f97316, #ea6c0a)",
                    color: "#fff", fontSize: 10, fontWeight: 800, letterSpacing: "0.1em",
                    textTransform: "uppercase", padding: "5px 16px", borderRadius: 99, whiteSpace: "nowrap",
                  }}>
                    Most popular
                  </div>
                )}

                <div style={{ marginBottom: 24 }}>
                  <p style={{ fontSize: 11, fontWeight: 800, letterSpacing: "0.12em", textTransform: "uppercase", color: t.muted, marginBottom: 8 }}>
                    {plan.tier}
                  </p>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                    <span style={{ fontSize: 52, fontWeight: 900, color: t.text, letterSpacing: "-0.04em", lineHeight: 1 }}>{plan.price}</span>
                    {plan.period && <span style={{ color: t.muted, fontWeight: 500, fontSize: 16 }}>{plan.period}</span>}
                  </div>
                  <p style={{ color: t.body, fontSize: 13, marginTop: 8 }}>{plan.description}</p>
                </div>

                <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 12, flex: 1, marginBottom: 28 }}>
                  {plan.features.map((f) => (
                    <li key={f} style={{ display: "flex", alignItems: "flex-start", gap: 10, fontSize: 13, color: t.body }}>
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" style={{ marginTop: 1, flexShrink: 0 }}>
                        <path d="M2.5 7l3 3L11.5 4" stroke={plan.accent ? t.orange : "#16a34a"} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                      {f}
                    </li>
                  ))}
                </ul>

                <Link href={plan.href}>
                  <motion.span
                    whileHover={plan.accent ? { scale: 1.02, boxShadow: t.orangeGlow } : { scale: 1.01 }}
                    whileTap={{ scale: 0.97 }}
                    transition={{ type: "spring", stiffness: 400, damping: 25 }}
                    style={{
                      display: "block", textAlign: "center", fontWeight: 700,
                      padding: "13px 0", borderRadius: 12, fontSize: 14, cursor: "pointer", letterSpacing: "-0.01em",
                      ...(plan.accent ? {
                        background: t.orange, color: "#fff",
                        boxShadow: "0 4px 16px rgba(249,115,22,0.25)",
                      } : {
                        background: t.bg2, border: `1px solid ${t.border}`, color: t.text,
                      }),
                    }}
                  >
                    {plan.cta}
                  </motion.span>
                </Link>
              </motion.div>
            </StaggerItem>
          ))}
        </StaggerGroup>
      </div>
    </section>
  );
}

function Integrations() {
  const t = useT();
  return (
    <section style={{ padding: "80px 24px", background: t.bg, borderTop: `1px solid ${t.border}` }}>
      <div style={{ maxWidth: 1000, margin: "0 auto" }}>
        <Reveal>
          <div style={{ textAlign: "center", marginBottom: 48 }}>
            <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.14em", textTransform: "uppercase", color: t.orange, marginBottom: 12 }}>
              Integrations
            </p>
            <h2 style={{ fontSize: "clamp(28px, 4vw, 40px)", fontWeight: 900, color: t.text, letterSpacing: "-0.04em", marginBottom: 12 }}>
              Built on tools you already use
            </h2>
            <p style={{ color: t.body, fontSize: 16 }}>
              From CRM to contracts, outreach to analytics — TradeBuilt plugs into the tools your agency already runs on.
            </p>
          </div>
        </Reveal>

        <StaggerGroup style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 12 }}>
          {INTEGRATIONS.map((item) => (
            <StaggerItem key={item.name}>
              <motion.div
                whileHover={{ y: -3, boxShadow: t.shadowHover }}
                transition={{ type: "spring", stiffness: 340, damping: 24 }}
                style={{
                  display: "flex", alignItems: "center", gap: 10,
                  background: t.card, border: `1px solid ${t.border}`, boxShadow: t.shadow,
                  borderRadius: 12, padding: "10px 16px 10px 10px",
                }}
              >
                <div style={{
                  width: 34, height: 34, borderRadius: 8, flexShrink: 0,
                  background: item.bg, border: `1px solid ${item.color}22`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontWeight: 900, fontSize: 13, color: item.color, letterSpacing: "-0.02em",
                }}>
                  {item.letter}
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: t.text, lineHeight: 1.2 }}>{item.name}</div>
                  <div style={{ fontSize: 11, color: t.muted, fontWeight: 500 }}>{item.tag}</div>
                </div>
              </motion.div>
            </StaggerItem>
          ))}
        </StaggerGroup>
      </div>
    </section>
  );
}

function FinalCTA() {
  const t = useT();
  const { scrollY } = useScroll();
  const blobY = useTransform(scrollY, [800, 2400], [0, -100]);

  return (
    <section style={{ padding: "110px 24px", background: t.bg2, borderTop: `1px solid ${t.border}`, position: "relative", overflow: "hidden" }}>
      <motion.div style={{
        y: blobY,
        position: "absolute", top: "-40%", left: "50%", transform: "translateX(-50%)",
        width: 900, height: 700, borderRadius: "50%", filter: "blur(80px)",
        background: "radial-gradient(ellipse, rgba(249,115,22,0.20) 0%, rgba(251,191,36,0.10) 45%, transparent 70%)",
        pointerEvents: "none",
      }} />
      <Reveal>
        <div style={{ maxWidth: 600, margin: "0 auto", textAlign: "center", position: "relative" }}>
          <h2 style={{ fontSize: "clamp(36px, 5vw, 54px)", fontWeight: 900, color: t.text, letterSpacing: "-0.04em", lineHeight: 1.05, marginBottom: 20 }}>
            Ready to land your
            <br />
            <span style={{
              background: "linear-gradient(135deg, #f97316 0%, #fb923c 100%)",
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text",
            }}>
              first trade client?
            </span>
          </h2>
          <p style={{ color: t.body, fontSize: 17, marginBottom: 36, lineHeight: 1.6 }}>
            Generate a free demo site for any local business right now. No signup required.
          </p>
          <Link href="/generate">
            <motion.span
              whileHover={{ scale: 1.03, boxShadow: "0 12px 40px rgba(249,115,22,0.35)" }}
              whileTap={{ scale: 0.97 }}
              transition={{ type: "spring", stiffness: 380, damping: 26 }}
              style={{
                display: "inline-flex", alignItems: "center", gap: 10,
                background: t.orange, color: "#fff", fontWeight: 800, fontSize: 17,
                padding: "16px 36px", borderRadius: 14, letterSpacing: "-0.02em", cursor: "pointer",
                boxShadow: "0 6px 24px rgba(249,115,22,0.28)",
              }}
            >
              Generate a demo site — free
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M3.5 9h11M10 4.5l4.5 4.5-4.5 4.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </motion.span>
          </Link>
        </div>
      </Reveal>
    </section>
  );
}

function Footer() {
  const t = useT();
  return (
    <footer style={{ borderTop: `1px solid ${t.border}`, background: t.card, padding: "32px 24px" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto", display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <TBIcon size={18} />
          <span style={{ fontWeight: 900, fontSize: 15, color: t.text, letterSpacing: "-0.03em" }}>TradeBuilt</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
          <Link href="/generate" style={{ fontSize: 13, color: t.muted, textDecoration: "none" }}>Generator</Link>
          <Link href="/dashboard" style={{ fontSize: 13, color: t.muted, textDecoration: "none" }}>Dashboard</Link>
          <Link href="/billing" style={{ fontSize: 13, color: t.muted, textDecoration: "none" }}>Pricing</Link>
        </div>
        <p style={{ fontSize: 12, color: t.muted }}>© {new Date().getFullYear()} TradeBuilt. Built to close.</p>
      </div>
    </footer>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function HomePage() {
  return (
    <ThemeProvider>
      <PageWrapper>
        <div>
          <Nav />
          <main>
            <Hero />
            <StatsBar />
            <TradesRow />
            <Features />
            <Process />
            <Pricing />
            <Integrations />
            <FinalCTA />
          </main>
          <Footer />
        </div>
      </PageWrapper>
    </ThemeProvider>
  );
}
