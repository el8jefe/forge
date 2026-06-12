"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ease, StaggerGroup, StaggerItem } from "@/components/ui/motion";
import { TBIcon } from "@/components/ui/logo";
import { ThemeProvider, ThemeToggle, useT } from "@/lib/theme";
import { useAuthGuard } from "@/lib/auth";

const STEPS = [
  {
    n: "01",
    icon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
        <circle cx="11" cy="11" r="9" stroke="#f97316" strokeWidth="1.5"/>
        <path d="M7 11l3 3 5-5" stroke="#f97316" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    title: "Find a trade business",
    desc: "Type any business name and city — HVAC, plumber, electrician, roofer, landscaper. Anywhere in the US.",
  },
  {
    n: "02",
    icon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
        <rect x="3" y="3" width="16" height="16" rx="3" stroke="#f97316" strokeWidth="1.5"/>
        <path d="M7 8h8M7 11h5M7 14h3" stroke="#f97316" strokeWidth="1.5" strokeLinecap="round"/>
      </svg>
    ),
    title: "Get a full demo site",
    desc: "TradeBuilt generates a complete, mobile-ready website with professional copy and a lead temperature score in under 5 seconds.",
  },
  {
    n: "03",
    icon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
        <path d="M19 3L3 9.5l7 2 2 7L19 3z" stroke="#f97316" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    title: "Send the pitch",
    desc: "One click sends a personalized cold email with the demo link. The business sees what their new site could look like — before you even get on a call.",
  },
  {
    n: "04",
    icon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
        <path d="M11 2v4M11 16v4M4.93 4.93l2.83 2.83M14.24 14.24l2.83 2.83M2 11h4M16 11h4M4.93 17.07l2.83-2.83M14.24 7.76l2.83-2.83" stroke="#f97316" strokeWidth="1.5" strokeLinecap="round"/>
      </svg>
    ),
    title: "Close the client",
    desc: "Track every lead in the pipeline. Follow up, mark won, collect the retainer. Repeat for the next city.",
  },
];

function WelcomeContent() {
  const checking = useAuthGuard();
  const t = useT();
  if (checking) return null;
  return (
    <div style={{ minHeight: "100vh", background: t.bg }}>
      {/* Blob */}
      <div style={{
        position: "fixed", top: "-20%", right: "-10%", width: 800, height: 800,
        borderRadius: "50%", filter: "blur(100px)", pointerEvents: "none", zIndex: 0,
        background: "radial-gradient(circle, rgba(249,115,22,0.18) 0%, transparent 65%)",
      }} />

      {/* Nav */}
      <nav style={{
        position: "sticky", top: 0, zIndex: 50,
        borderBottom: `1px solid ${t.border}`,
        background: t.navBg,
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
      }}>
        <div style={{ maxWidth: 960, margin: "0 auto", padding: "0 24px", height: 60, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <TBIcon size={20} />
            <span style={{ fontWeight: 900, fontSize: 16, letterSpacing: "-0.04em", color: t.text }}>TradeBuilt</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <ThemeToggle />
            <Link href="/dashboard" style={{ fontSize: 13, color: t.muted, textDecoration: "none", fontWeight: 500 }}>
              Skip to dashboard →
            </Link>
          </div>
        </div>
      </nav>

      <div style={{ position: "relative", zIndex: 1, maxWidth: 800, margin: "0 auto", padding: "64px 24px 100px" }}>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: ease.smooth }}
          style={{ textAlign: "center", marginBottom: 64 }}
        >
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 8, marginBottom: 24,
            background: "rgba(249,115,22,0.08)", border: "1px solid rgba(249,115,22,0.18)",
            padding: "6px 16px", borderRadius: 99,
          }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: t.orange, display: "block" }} />
            <span style={{ fontSize: 12, fontWeight: 700, color: t.orange, letterSpacing: "0.06em", textTransform: "uppercase" }}>
              Account created
            </span>
          </div>

          <h1 style={{ fontSize: "clamp(36px, 5vw, 56px)", fontWeight: 900, color: t.text, letterSpacing: "-0.04em", lineHeight: 1.05, marginBottom: 16 }}>
            You&apos;re in.
            <br />
            <span style={{
              background: "linear-gradient(135deg, #f97316 0%, #fb923c 55%, #fbbf24 100%)",
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text",
            }}>
              Here&apos;s how this works.
            </span>
          </h1>
          <p style={{ fontSize: 17, color: t.body, maxWidth: 480, margin: "0 auto", lineHeight: 1.65 }}>
            TradeBuilt is your outbound sales machine for landing trade clients.
            Watch how it works, then try it yourself.
          </p>
        </motion.div>

        {/* Video placeholder */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.15, ease: ease.smooth }}
          style={{ marginBottom: 64 }}
        >
          <div style={{
            position: "relative", width: "100%", paddingBottom: "56.25%",
            background: t.card, border: `1px solid ${t.border}`, borderRadius: 20,
            boxShadow: t.shadow, overflow: "hidden",
          }}>
            {/* Video goes here — replace src with real Loom/YouTube embed URL */}
            <div style={{
              position: "absolute", inset: 0, display: "flex", flexDirection: "column",
              alignItems: "center", justifyContent: "center", gap: 16,
            }}>
              <motion.div
                whileHover={{ scale: 1.08 }}
                whileTap={{ scale: 0.96 }}
                style={{
                  width: 72, height: 72, borderRadius: "50%",
                  background: t.orange, display: "flex", alignItems: "center", justifyContent: "center",
                  cursor: "pointer", boxShadow: "0 8px 32px rgba(249,115,22,0.35)",
                }}
              >
                <svg width="28" height="28" viewBox="0 0 28 28" fill="none" style={{ marginLeft: 4 }}>
                  <path d="M8 6l16 8-16 8V6z" fill="#fff"/>
                </svg>
              </motion.div>
              <p style={{ fontSize: 14, color: t.muted, fontWeight: 500 }}>Demo video — coming soon</p>
            </div>
          </div>
        </motion.div>

        {/* Steps */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.25, ease: ease.smooth }}
          style={{ marginBottom: 16 }}
        >
          <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase", color: t.orange, marginBottom: 24, textAlign: "center" }}>
            The 4-step process
          </p>
        </motion.div>

        <StaggerGroup style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 14, marginBottom: 64 }}>
          {STEPS.map((s) => (
            <StaggerItem key={s.n}>
              <div style={{
                background: t.card, border: `1px solid ${t.border}`,
                borderRadius: 16, padding: "22px 20px", boxShadow: t.shadow,
                display: "flex", gap: 16, alignItems: "flex-start",
              }}>
                <div style={{
                  display: "flex", alignItems: "center", justifyContent: "center",
                  width: 40, height: 40, borderRadius: 10, flexShrink: 0,
                  background: "rgba(249,115,22,0.08)", border: "1px solid rgba(249,115,22,0.15)",
                }}>
                  {s.icon}
                </div>
                <div>
                  <div style={{ fontSize: 10, fontWeight: 800, color: t.muted, letterSpacing: "0.1em", marginBottom: 4 }}>STEP {s.n}</div>
                  <h3 style={{ fontSize: 14, fontWeight: 700, color: t.text, marginBottom: 6, letterSpacing: "-0.02em" }}>{s.title}</h3>
                  <p style={{ fontSize: 13, color: t.body, lineHeight: 1.6 }}>{s.desc}</p>
                </div>
              </div>
            </StaggerItem>
          ))}
        </StaggerGroup>

        {/* Pricing CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4, ease: ease.smooth }}
        >
          <div style={{
            background: t.card, border: `1.5px solid rgba(249,115,22,0.25)`,
            borderRadius: 22, padding: "40px 36px", textAlign: "center",
            boxShadow: "0 8px 32px rgba(249,115,22,0.10), 0 2px 8px rgba(120,80,30,0.06)",
          }}>
            <p style={{ fontSize: 11, fontWeight: 800, letterSpacing: "0.12em", textTransform: "uppercase", color: t.muted, marginBottom: 12 }}>
              Start closing
            </p>
            <h2 style={{ fontSize: "clamp(28px, 4vw, 40px)", fontWeight: 900, color: t.text, letterSpacing: "-0.04em", marginBottom: 8 }}>
              $49 <span style={{ fontSize: 18, fontWeight: 500, color: t.muted }}>/month</span>
            </h2>
            <p style={{ fontSize: 15, color: t.body, marginBottom: 8, lineHeight: 1.6, maxWidth: 420, margin: "0 auto 28px" }}>
              Unlimited AI generation, full CRM pipeline, one-click email outreach.
              Cancel anytime — no contracts.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: 12, alignItems: "center" }}>
              <Link href="/billing">
                <motion.span
                  whileHover={{ scale: 1.03, boxShadow: "0 8px 32px rgba(249,115,22,0.35)" }}
                  whileTap={{ scale: 0.97 }}
                  transition={{ type: "spring", stiffness: 380, damping: 26 }}
                  style={{
                    display: "inline-flex", alignItems: "center", gap: 10,
                    background: t.orange, color: "#fff", fontWeight: 800, fontSize: 16,
                    padding: "14px 36px", borderRadius: 12, cursor: "pointer",
                    letterSpacing: "-0.01em", boxShadow: "0 4px 20px rgba(249,115,22,0.28)",
                  }}
                >
                  Get started — $49/mo
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </motion.span>
              </Link>

              <Link href="/generate">
                <span style={{ fontSize: 13, color: t.muted, textDecoration: "none", fontWeight: 500, cursor: "pointer" }}>
                  Try the generator first →
                </span>
              </Link>
            </div>
          </div>
        </motion.div>

      </div>
    </div>
  );
}

export default function WelcomePage() {
  return (
    <ThemeProvider>
      <WelcomeContent />
    </ThemeProvider>
  );
}
