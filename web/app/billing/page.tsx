"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ease, StaggerGroup, StaggerItem } from "@/components/ui/motion";
import { TBIcon } from "@/components/ui/logo";
import { useAuthGuard, getAccessToken } from "@/lib/auth";

const PLANS = [
  {
    tier: "Free",
    price: "$0",
    period: "",
    description: "Get started, no card needed.",
    features: [
      "10 template sites per month",
      "Website quality scoring",
      "Download HTML demos",
      "Save leads to pipeline",
      "Lead temperature rating",
    ],
    cta: "Current plan",
    href: null,
    accent: false,
  },
  {
    tier: "Pro",
    price: "$49",
    period: "/mo",
    description: "Everything you need to close at scale.",
    features: [
      "Everything in Free",
      "Unlimited AI generation",
      "Full dual-layer scoring",
      "1-click email outreach",
      "Complete CRM pipeline",
      "Priority support",
    ],
    cta: "Upgrade to Pro",
    href: "/api/stripe/checkout",
    accent: true,
  },
];

export default function BillingPage() {
  const checking = useAuthGuard();
  const [upgrading, setUpgrading] = useState(false);
  const [upgradeError, setUpgradeError] = useState<string | null>(null);

  if (checking) return null;

  async function handleUpgrade() {
    setUpgrading(true);
    setUpgradeError(null);
    const token = await getAccessToken();
    const res = await fetch("/api/stripe/checkout", {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    const data = await res.json() as { url?: string; error?: string };
    if (data.url) {
      window.location.href = data.url;
    } else {
      setUpgradeError(data.error ?? "Something went wrong");
      setUpgrading(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: "#0A0A0B" }}>
      {/* Nav */}
      <nav style={{
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        background: "rgba(10,10,11,0.9)",
        backdropFilter: "blur(20px)",
        position: "sticky", top: 0, zIndex: 40,
      }}>
        <div style={{ maxWidth: 900, margin: "0 auto", padding: "0 24px", height: 64, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Link href="/" style={{ textDecoration: "none" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <TBIcon size={20} />
              <span style={{ fontWeight: 900, fontSize: 16, letterSpacing: "-0.04em", color: "#f4f4f5" }}>TradeBuilt</span>
            </div>
          </Link>
          <Link href="/generate" style={{ fontSize: 13, fontWeight: 600, color: "#71717a", textDecoration: "none" }}>Generator →</Link>
        </div>
      </nav>

      <main style={{ maxWidth: 780, margin: "0 auto", padding: "60px 24px 80px" }}>
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: ease.smooth }}
          style={{ textAlign: "center", marginBottom: 48 }}
        >
          <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.14em", textTransform: "uppercase", color: "#f97316", marginBottom: 12 }}>
            Pricing
          </p>
          <h1 style={{ fontSize: "clamp(32px, 5vw, 48px)", fontWeight: 900, color: "#f4f4f5", letterSpacing: "-0.04em", marginBottom: 12 }}>
            Simple. No bullshit.
          </h1>
          <p style={{ fontSize: 16, color: "#71717a" }}>
            Start free. Upgrade when you land your first client.
          </p>
        </motion.div>

        <StaggerGroup style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 16 }}>
          {PLANS.map((plan) => (
            <StaggerItem key={plan.tier}>
              <div style={{
                background: "#111113",
                border: `1px solid ${plan.accent ? "rgba(249,115,22,0.3)" : "rgba(255,255,255,0.06)"}`,
                borderRadius: 20, padding: 32,
                height: "100%", boxSizing: "border-box",
                display: "flex", flexDirection: "column",
                ...(plan.accent ? { boxShadow: "0 0 40px rgba(249,115,22,0.1)" } : {}),
              }}>
                {plan.accent && (
                  <div style={{
                    display: "inline-block", alignSelf: "flex-start",
                    fontSize: 10, fontWeight: 800, letterSpacing: "0.1em", textTransform: "uppercase",
                    background: "linear-gradient(90deg, #f97316, #ea6c0a)", color: "#fff",
                    padding: "3px 12px", borderRadius: 99, marginBottom: 20,
                  }}>
                    Most popular
                  </div>
                )}

                <div style={{ marginBottom: 24 }}>
                  <p style={{ fontSize: 10, fontWeight: 800, letterSpacing: "0.14em", textTransform: "uppercase", color: "#52525b", marginBottom: 8 }}>
                    {plan.tier}
                  </p>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                    <span style={{ fontSize: 48, fontWeight: 900, color: "#f4f4f5", letterSpacing: "-0.04em", lineHeight: 1 }}>{plan.price}</span>
                    {plan.period && <span style={{ fontSize: 15, color: "#52525b", fontWeight: 500 }}>{plan.period}</span>}
                  </div>
                  <p style={{ fontSize: 13, color: "#71717a", marginTop: 8 }}>{plan.description}</p>
                </div>

                <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 12, flex: 1, marginBottom: 28 }}>
                  {plan.features.map((f) => (
                    <li key={f} style={{ display: "flex", alignItems: "flex-start", gap: 10, fontSize: 13, color: "#a1a1aa" }}>
                      <svg style={{ width: 13, height: 13, flexShrink: 0, marginTop: 1 }} viewBox="0 0 13 13" fill="none">
                        <path d="M2 6.5l3 3L11 3.5" stroke={plan.accent ? "#f97316" : "#22c55e"} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                      {f}
                    </li>
                  ))}
                </ul>

                {plan.href ? (
                  <>
                  <motion.button
                    whileHover={!upgrading ? { scale: 1.01, boxShadow: "0 0 28px rgba(249,115,22,0.35)" } : {}}
                    whileTap={{ scale: 0.97 }}
                    onClick={handleUpgrade}
                    disabled={upgrading}
                    style={{
                      width: "100%", padding: "13px 0",
                      background: upgrading ? "rgba(249,115,22,0.4)" : "#f97316", color: "#fff",
                      fontSize: 14, fontWeight: 800, border: "none", borderRadius: 10,
                      cursor: upgrading ? "not-allowed" : "pointer", letterSpacing: "-0.01em",
                      display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
                    }}
                  >
                    {upgrading && (
                      <svg className="animate-spin" style={{ width: 14, height: 14 }} viewBox="0 0 24 24" fill="none">
                        <circle style={{ opacity: 0.25 }} cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3"/>
                        <path style={{ opacity: 0.75 }} fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                      </svg>
                    )}
                    {upgrading ? "Redirecting…" : plan.cta}
                  </motion.button>
                  {upgradeError && (
                    <p style={{ fontSize: 12, color: "#f87171", marginTop: 8, textAlign: "center" }}>{upgradeError}</p>
                  )}
                  </>
                ) : (
                  <div style={{
                    width: "100%", padding: "13px 0", textAlign: "center",
                    background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)",
                    fontSize: 13, fontWeight: 700, color: "#52525b",
                    borderRadius: 10,
                  }}>
                    {plan.cta}
                  </div>
                )}
              </div>
            </StaggerItem>
          ))}
        </StaggerGroup>

        <p style={{ textAlign: "center", fontSize: 13, color: "#3f3f46", marginTop: 28 }}>
          Questions?{" "}
          <Link href="mailto:support@tradebuilt.io" style={{ color: "#52525b", textDecoration: "underline" }}>
            support@tradebuilt.io
          </Link>
        </p>
      </main>
    </div>
  );
}
