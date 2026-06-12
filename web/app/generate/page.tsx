"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { PageWrapper, ease } from "@/components/ui/motion";
import { TBIcon } from "@/components/ui/logo";
import { addLead } from "@/lib/crm";
import type { GenerateSiteResponse } from "@/lib/types";
import { ThemeProvider, ThemeToggle, useT } from "@/lib/theme";
import { useAuthGuard } from "@/lib/auth";
import { authFetch } from "@/lib/fetch-auth";

// ── Loading steps ─────────────────────────────────────────────────────────────
const STEPS = {
  template: [
    "Finding business data",
    "Detecting trade and location",
    "Selecting color theme",
    "Building site structure",
    "Finalizing layout",
  ],
  ai: [
    "Searching for business data",
    "Analyzing market context",
    "Writing headline copy",
    "Crafting service descriptions",
    "Scoring conversion rate",
  ],
};

const TEMP_COLORS: Record<string, { bg: string; text: string; dot: string; label: string }> = {
  burning: { bg: "rgba(239,68,68,0.12)", text: "#f87171", dot: "#ef4444", label: "Burning Hot" },
  hot:     { bg: "rgba(249,115,22,0.12)", text: "#fb923c", dot: "#f97316", label: "Hot" },
  warm:    { bg: "rgba(245,158,11,0.12)", text: "#fbbf24", dot: "#f59e0b", label: "Warm" },
  cold:    { bg: "rgba(113,113,122,0.12)", text: "#a1a1aa", dot: "#71717a", label: "Cold" },
};

// ── Score bar ─────────────────────────────────────────────────────────────────
function ScoreBar({ label, value }: { label: string; value: number }) {
  const t = useT();
  const pct = (value / 10) * 100;
  const color = value >= 8 ? "#22c55e" : value >= 6 ? "#f97316" : "#ef4444";
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: t.muted, textTransform: "capitalize", letterSpacing: "0.04em" }}>{label}</span>
        <span style={{ fontSize: 12, fontWeight: 900, color: t.text }}>
          {value.toFixed(0)}<span style={{ color: t.muted, fontWeight: 500 }}>/10</span>
        </span>
      </div>
      <div style={{ height: 3, background: t.border, borderRadius: 99, overflow: "hidden" }}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, delay: 0.2, ease: ease.smooth }}
          style={{ height: "100%", borderRadius: 99, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

// ── Dark skeleton ─────────────────────────────────────────────────────────────
function Skeleton({ style = {} }: { style?: React.CSSProperties }) {
  const t = useT();
  return (
    <div
      style={{
        borderRadius: 8,
        background: `linear-gradient(90deg, ${t.skeletonFrom} 25%, ${t.skeletonTo} 50%, ${t.skeletonFrom} 75%)`,
        backgroundSize: "200% 100%",
        animation: "shimmer 1.6s ease-in-out infinite",
        ...style,
      }}
    />
  );
}

// ── Loading state ─────────────────────────────────────────────────────────────
function LoadingCard({ mode, step }: { mode: "template" | "ai"; step: number }) {
  const t = useT();
  const steps = STEPS[mode];
  return (
    <motion.div
      key="loading"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.35, ease: ease.smooth }}
      style={{
        background: t.card,
        border: `1px solid ${t.border}`,
        borderRadius: 16,
        padding: 28,
      }}
    >
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 16 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: "linear-gradient(135deg, #f97316, #ea6c0a)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 4px 16px rgba(249,115,22,0.3)",
            flexShrink: 0,
          }}>
            <svg className="animate-spin" style={{ width: 18, height: 18, color: "#fff" }} viewBox="0 0 24 24" fill="none">
              <circle style={{ opacity: 0.25 }} cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
              <path style={{ opacity: 0.75 }} fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
          <div>
            <p style={{ fontSize: 13, fontWeight: 700, color: t.text, letterSpacing: "-0.01em" }}>
              {mode === "ai" ? "Claude is writing your copy" : "Building your site"}
            </p>
            <p style={{ fontSize: 12, color: t.muted, marginTop: 2 }}>{steps[step]}</p>
          </div>
        </div>

        <div style={{ display: "flex", gap: 6 }}>
          {steps.map((_, i) => (
            <motion.div
              key={i}
              animate={{
                width: i <= step ? 24 : 10,
                backgroundColor: i <= step ? "#f97316" : t.border,
              }}
              transition={{ duration: 0.3 }}
              style={{ height: 3, borderRadius: 99 }}
            />
          ))}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        <Skeleton style={{ height: 16, width: "60%" }} />
        <Skeleton style={{ height: 10, width: "100%" }} />
        <Skeleton style={{ height: 10, width: "80%" }} />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, paddingTop: 8 }}>
          <Skeleton style={{ height: 60 }} />
          <Skeleton style={{ height: 60 }} />
          <Skeleton style={{ height: 60 }} />
        </div>
      </div>
    </motion.div>
  );
}

// ── Results ───────────────────────────────────────────────────────────────────
function ResultCard({ result, onSaveToCrm, savedToCrm }: {
  result: GenerateSiteResponse;
  onSaveToCrm: () => void;
  savedToCrm: boolean;
}) {
  const temp = result.score?.lead_quality?.temperature_short ?? "cold";
  const tempConf = TEMP_COLORS[temp] ?? TEMP_COLORS.cold;
  const t = useT();
  const [emailForm, setEmailForm] = useState<"idle" | "open" | "sending" | "sent" | "error">("idle");
  const [toEmail, setToEmail] = useState("");
  const [toName, setToName] = useState(result.business.name);
  const [emailError, setEmailError] = useState("");

  async function handleSendEmail(e: React.FormEvent) {
    e.preventDefault();
    setEmailForm("sending");
    setEmailError("");
    try {
      const res = await authFetch("/api/send-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to_email: toEmail,
          to_name: toName,
          business_name: result.business.name,
          service_type: result.business.service_type,
          city: result.business.city,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setEmailError((err as { error?: string }).error ?? "Failed to send");
        setEmailForm("error");
      } else {
        setEmailForm("sent");
      }
    } catch {
      setEmailError("Network error — please try again.");
      setEmailForm("error");
    }
  }

  return (
    <motion.div
      key="result"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.45, ease: ease.smooth }}
      style={{ display: "flex", flexDirection: "column", gap: 12 }}
    >
      {/* Business header */}
      <div style={{
        background: t.card,
        border: `1px solid ${t.border}`,
        boxShadow: t.shadow,
        borderRadius: 16,
        padding: 24,
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
          <div>
            <h2 style={{ fontWeight: 900, fontSize: 20, color: t.text, letterSpacing: "-0.03em", marginBottom: 4 }}>
              {result.business.name}
            </h2>
            <p style={{ fontSize: 13, color: t.muted }}>
              {result.business.service_type} · {result.business.city}
              {result.business.state ? `, ${result.business.state}` : ""}
            </p>
            {result.score?.lead_quality && (
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
                <span style={{
                  display: "inline-flex", alignItems: "center", gap: 6,
                  background: tempConf.bg, color: tempConf.text,
                  fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase",
                  padding: "4px 10px", borderRadius: 99,
                }}>
                  <span style={{ width: 5, height: 5, borderRadius: "50%", background: tempConf.dot, display: "block" }} />
                  {tempConf.label}
                </span>
                <span style={{ fontSize: 12, color: t.muted }}>{result.score.lead_quality.reason}</span>
              </div>
            )}
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 42, fontWeight: 900, color: t.text, letterSpacing: "-0.04em", lineHeight: 1 }}>
              {result.score.score.toFixed(1)}
            </div>
            <div style={{ fontSize: 11, color: t.muted, marginTop: 2 }}>site score / 10</div>
            {result.cached && (
              <span style={{
                display: "inline-block", marginTop: 6,
                fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase",
                color: t.muted, background: t.tabBg,
                padding: "2px 8px", borderRadius: 99,
              }}>cached</span>
            )}
          </div>
        </div>
      </div>

      {/* Score breakdown */}
      <div style={{
        background: t.card,
        border: `1px solid ${t.border}`,
        boxShadow: t.shadow,
        borderRadius: 16,
        padding: 24,
      }}>
        <h3 style={{ fontSize: 11, fontWeight: 800, letterSpacing: "0.1em", textTransform: "uppercase", color: t.muted, marginBottom: 16 }}>Score breakdown</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px 32px" }}>
          {Object.entries(result.score.breakdown).map(([dim, val]) => (
            <ScoreBar key={dim} label={dim} value={val as number} />
          ))}
        </div>
        <p style={{ fontSize: 13, color: t.body, marginTop: 16, paddingTop: 16, borderTop: `1px solid ${t.subtleBorder}`, lineHeight: 1.6 }}>
          {result.score.feedback}
        </p>
        {result.score.improvements.length > 0 && (
          <ul style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8, listStyle: "none", padding: 0 }}>
            {result.score.improvements.map((tip, i) => (
              <li key={i} style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 12, color: t.muted }}>
                <svg style={{ width: 12, height: 12, color: "#f97316", flexShrink: 0, marginTop: 1 }} viewBox="0 0 12 12" fill="none">
                  <path d="M2 6h8M7 3l3 3-3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                {tip}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Site preview */}
      {result.html && (
        <div style={{
          background: "#111113",
          border: "1px solid rgba(255,255,255,0.07)",
          borderRadius: 16,
          overflow: "hidden",
        }}>
          {/* Browser chrome */}
          <div style={{
            display: "flex", alignItems: "center", gap: 12,
            padding: "10px 16px",
            borderBottom: "1px solid rgba(255,255,255,0.05)",
            background: "#18181b",
          }}>
            <div style={{ display: "flex", gap: 6 }}>
              {["#ef4444", "#f59e0b", "#22c55e"].map((c) => (
                <div key={c} style={{ width: 10, height: 10, borderRadius: "50%", background: c, opacity: 0.5 }} />
              ))}
            </div>
            <div style={{
              flex: 1, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)",
              borderRadius: 6, padding: "4px 12px", fontSize: 11, color: "#52525b",
              fontFamily: "monospace",
            }}>
              {result.business.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}.com
            </div>
            {result.mode && (
              <span style={{
                fontSize: 10, fontWeight: 800, letterSpacing: "0.08em", textTransform: "uppercase",
                padding: "3px 8px", borderRadius: 99,
                background: result.mode === "ai" ? "rgba(249,115,22,0.15)" : "rgba(37,99,235,0.15)",
                color: result.mode === "ai" ? "#fb923c" : "#60a5fa",
              }}>
                {result.mode === "ai" ? "AI" : "Template"}
              </span>
            )}
          </div>
          <iframe
            srcDoc={result.html}
            style={{ width: "100%", border: 0, height: 600, display: "block" }}
            title="Site Preview"
            sandbox="allow-scripts"
          />
        </div>
      )}

      {/* Actions */}
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10 }}>

        {/* Send email button */}
        {emailForm === "sent" ? (
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            style={{
              display: "inline-flex", alignItems: "center", gap: 8,
              background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.25)",
              color: "#16a34a", fontSize: 13, fontWeight: 700,
              padding: "10px 20px", borderRadius: 10,
            }}
          >
            <svg style={{ width: 14, height: 14 }} viewBox="0 0 14 14" fill="none">
              <path d="M2 7l3 3L12 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Email sent
          </motion.div>
        ) : (
          <motion.button
            whileHover={{ scale: 1.02, boxShadow: "0 4px 20px rgba(249,115,22,0.25)" }}
            whileTap={{ scale: 0.97 }}
            onClick={() => setEmailForm(emailForm === "open" || emailForm === "error" ? "idle" : "open")}
            style={{
              background: "#f97316", color: "#fff",
              fontSize: 13, fontWeight: 700,
              padding: "10px 20px", borderRadius: 10,
              border: "none", cursor: "pointer", letterSpacing: "-0.01em",
              display: "flex", alignItems: "center", gap: 7,
            }}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M13 1L1 6l5 2.5L8.5 13 13 1z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Send cold email
          </motion.button>
        )}

        {!savedToCrm ? (
          <motion.button
            whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}
            onClick={onSaveToCrm}
            style={{
              background: t.card, border: `1px solid ${t.border}`,
              boxShadow: t.shadow,
              color: t.text, fontSize: 13, fontWeight: 700,
              padding: "10px 20px", borderRadius: 10,
              cursor: "pointer", letterSpacing: "-0.01em",
            }}
          >
            Save to pipeline
          </motion.button>
        ) : (
          <Link href="/dashboard">
            <motion.span
              initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
              style={{
                display: "inline-flex", alignItems: "center", gap: 8,
                background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.25)",
                color: "#16a34a", fontSize: 13, fontWeight: 700,
                padding: "10px 20px", borderRadius: 10, cursor: "pointer",
              }}
            >
              <svg style={{ width: 14, height: 14 }} viewBox="0 0 14 14" fill="none">
                <path d="M2 7l3 3L12 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Saved — View pipeline
            </motion.span>
          </Link>
        )}

        {result.html && (
          <motion.button
            whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.97 }}
            onClick={() => {
              const blob = new Blob([result.html!], { type: "text/html" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `${result.business.name.replace(/\s+/g, "-").toLowerCase()}-demo.html`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            style={{
              background: "transparent", border: `1px solid ${t.border}`,
              color: t.muted, fontSize: 13, fontWeight: 600,
              padding: "10px 20px", borderRadius: 10, cursor: "pointer",
            }}
          >
            Download HTML
          </motion.button>
        )}
      </div>

      {/* Email form — expands inline */}
      <AnimatePresence>
        {(emailForm === "open" || emailForm === "sending" || emailForm === "error") && (
          <motion.div
            initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.25, ease: ease.smooth }}
            style={{ overflow: "hidden" }}
          >
            <form onSubmit={handleSendEmail} style={{
              background: t.card, border: `1px solid ${t.border}`,
              borderRadius: 14, padding: 20,
              boxShadow: t.shadow,
            }}>
              <p style={{ fontSize: 13, fontWeight: 700, color: t.text, marginBottom: 14 }}>
                Send outreach email for {result.business.name}
              </p>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 12 }}>
                {[
                  { label: "Their email", value: toEmail, onChange: setToEmail, placeholder: "owner@business.com", type: "email" },
                  { label: "Contact name", value: toName, onChange: setToName, placeholder: result.business.name, type: "text" },
                ].map((f) => (
                  <div key={f.label}>
                    <label style={{ display: "block", fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: t.muted, marginBottom: 6 }}>
                      {f.label}
                    </label>
                    <input
                      type={f.type} value={f.value} required
                      onChange={(e) => f.onChange(e.target.value)}
                      placeholder={f.placeholder}
                      disabled={emailForm === "sending"}
                      style={{
                        width: "100%", boxSizing: "border-box",
                        background: t.inputBg, border: `1px solid ${t.border}`,
                        borderRadius: 8, padding: "9px 12px",
                        fontSize: 13, color: t.text, outline: "none",
                      }}
                      onFocus={(e) => { e.target.style.borderColor = "rgba(249,115,22,0.4)"; }}
                      onBlur={(e) => { e.target.style.borderColor = t.border; }}
                    />
                  </div>
                ))}
              </div>
              {emailError && (
                <p style={{ fontSize: 12, color: "#ef4444", marginBottom: 10 }}>{emailError}</p>
              )}
              <div style={{ display: "flex", gap: 8 }}>
                <motion.button
                  type="submit" disabled={emailForm === "sending"}
                  whileHover={emailForm !== "sending" ? { scale: 1.02 } : {}}
                  whileTap={{ scale: 0.97 }}
                  style={{
                    flex: 1, padding: "10px 0",
                    background: emailForm === "sending" ? "rgba(249,115,22,0.4)" : "#f97316",
                    color: "#fff", fontWeight: 700, fontSize: 13, border: "none",
                    borderRadius: 8, cursor: emailForm === "sending" ? "not-allowed" : "pointer",
                    display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
                  }}
                >
                  {emailForm === "sending" && (
                    <svg className="animate-spin" style={{ width: 12, height: 12 }} viewBox="0 0 24 24" fill="none">
                      <circle style={{ opacity: 0.25 }} cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3"/>
                      <path style={{ opacity: 0.75 }} fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                  )}
                  {emailForm === "sending" ? "Sending…" : "Send email"}
                </motion.button>
                <button
                  type="button" onClick={() => { setEmailForm("idle"); setEmailError(""); }}
                  style={{ padding: "10px 16px", background: "transparent", border: `1px solid ${t.border}`, borderRadius: 8, fontSize: 13, color: t.muted, cursor: "pointer" }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function GeneratePage() {
  const checking = useAuthGuard();
  const t = useT();
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [mode, setMode] = useState<"template" | "ai">("template");
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);
  const [result, setResult] = useState<GenerateSiteResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savedToCrm, setSavedToCrm] = useState(false);

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !location.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setSavedToCrm(false);
    setStep(0);

    const steps = STEPS[mode];
    const interval = setInterval(() => {
      setStep((i) => (i < steps.length - 1 ? i + 1 : i));
    }, 900);

    try {
      const res = await authFetch("/api/generate-site", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), location: location.trim(), mode }),
      });
      clearInterval(interval);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setError((err as { error?: string }).error ?? "Something went wrong.");
        return;
      }
      const data: GenerateSiteResponse = await res.json();
      setResult(data);
    } catch {
      clearInterval(interval);
      setError("Network error — please try again.");
    } finally {
      clearInterval(interval);
      setLoading(false);
    }
  }

  function handleSaveToCrm() {
    if (!result) return;
    addLead(result.business, result.content, result.score, result.score?.lead_quality, undefined)
      .then(() => setSavedToCrm(true))
      .catch((err) => console.error("Save to CRM failed:", err?.message ?? err));
  }

  if (checking) return null;

  return (
    <ThemeProvider>
    <PageWrapper>
      {/* Nav */}
      <nav style={{
        borderBottom: `1px solid ${t.border}`,
        background: t.navBg,
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        position: "sticky", top: 0, zIndex: 40,
      }}>
        <div style={{ maxWidth: 900, margin: "0 auto", padding: "0 24px", height: 64, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Link href="/" style={{ textDecoration: "none" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <TBIcon size={20} />
              <span style={{ fontWeight: 900, fontSize: 16, letterSpacing: "-0.04em", color: t.text }}>TradeBuilt</span>
            </div>
          </Link>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <ThemeToggle />
            <Link href="/dashboard" style={{ fontSize: 13, fontWeight: 600, color: t.muted, textDecoration: "none" }}>
              Pipeline →
            </Link>
          </div>
        </div>
      </nav>

      <main style={{ maxWidth: 720, margin: "0 auto", padding: "60px 24px 80px" }}>
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: ease.smooth }}
          style={{ marginBottom: 40, textAlign: "center" }}
        >
          <h1 style={{ fontSize: "clamp(32px, 5vw, 44px)", fontWeight: 900, color: t.text, letterSpacing: "-0.04em", marginBottom: 10 }}>
            Generate a demo site
          </h1>
          <p style={{ color: t.body, fontSize: 16 }}>
            Any trade business. Any city. Results in seconds.
          </p>
        </motion.div>

        {/* Form card */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.1, ease: ease.smooth }}
          style={{
            background: t.card,
            border: `1px solid ${t.border}`,
            boxShadow: t.shadow,
            borderRadius: 18,
            padding: 28,
            marginBottom: 20,
          }}
        >
          <form onSubmit={handleGenerate}>
            {/* Mode toggle */}
            <div style={{
              display: "flex", gap: 6, padding: 6,
              background: t.bg2,
              border: `1px solid ${t.border}`,
              borderRadius: 12, marginBottom: 24,
            }}>
              {(["template", "ai"] as const).map((m) => (
                <motion.button
                  key={m}
                  type="button"
                  onClick={() => setMode(m)}
                  whileTap={{ scale: 0.97 }}
                  style={{
                    flex: 1,
                    display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
                    padding: "9px 16px", borderRadius: 8,
                    fontSize: 13, fontWeight: 700, border: "none", cursor: "pointer",
                    transition: "all 0.15s",
                    ...(mode === m ? {
                      background: t.card,
                      color: t.text,
                      boxShadow: t.shadow,
                    } : {
                      background: "transparent",
                      color: t.muted,
                    }),
                  }}
                >
                  {m === "template" ? (
                    <>
                      <svg style={{ width: 13, height: 13 }} viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="1" y="1" width="12" height="12" rx="2"/>
                        <path d="M1 5h12M5 5v8"/>
                      </svg>
                      Template
                      <span style={{ fontSize: 10, fontWeight: 700, color: "#52525b", letterSpacing: "0.06em" }}>FREE</span>
                    </>
                  ) : (
                    <>
                      <svg style={{ width: 13, height: 13 }} viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M7 1v2M7 11v2M1 7h2M11 7h2M3.22 3.22l1.41 1.41M9.36 9.36l1.42 1.42M3.22 10.78l1.41-1.41M9.36 4.64l1.42-1.42"/>
                        <circle cx="7" cy="7" r="2.5"/>
                      </svg>
                      AI Mode
                      <span style={{
                        fontSize: 10, fontWeight: 800, letterSpacing: "0.06em",
                        padding: "2px 7px", borderRadius: 99,
                        background: "linear-gradient(90deg, #f97316, #ea6c0a)",
                        color: "#fff",
                      }}>PRO</span>
                    </>
                  )}
                </motion.button>
              ))}
            </div>

            {/* Inputs */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
              {[
                { label: "Business name", placeholder: "Mike's Plumbing & Heating", value: name, onChange: (e: React.ChangeEvent<HTMLInputElement>) => setName(e.target.value) },
                { label: "City", placeholder: "Denver, CO", value: location, onChange: (e: React.ChangeEvent<HTMLInputElement>) => setLocation(e.target.value) },
              ].map((field) => (
                <div key={field.label}>
                  <label style={{ display: "block", fontSize: 11, fontWeight: 700, color: t.muted, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8 }}>
                    {field.label}
                  </label>
                  <input
                    type="text"
                    placeholder={field.placeholder}
                    value={field.value}
                    onChange={field.onChange}
                    disabled={loading}
                    required
                    style={{
                      width: "100%", boxSizing: "border-box",
                      background: t.inputBg,
                      border: `1px solid ${t.border}`,
                      borderRadius: 10, padding: "11px 14px",
                      fontSize: 14, color: t.text,
                      outline: "none", transition: "border-color 0.15s",
                    }}
                    onFocus={(e) => { e.target.style.borderColor = "rgba(249,115,22,0.4)"; }}
                    onBlur={(e) => { e.target.style.borderColor = t.border; }}
                  />
                </div>
              ))}
            </div>

            {/* Submit */}
            <motion.button
              type="submit"
              whileHover={(!loading && name.trim() && location.trim()) ? { scale: 1.01, boxShadow: "0 0 32px rgba(249,115,22,0.35)" } : {}}
              whileTap={{ scale: 0.98 }}
              disabled={loading || !name.trim() || !location.trim()}
              style={{
                width: "100%", padding: "14px 0",
                background: loading || !name.trim() || !location.trim() ? "rgba(249,115,22,0.3)" : "#f97316",
                color: "#fff", fontSize: 15, fontWeight: 800,
                border: "none", borderRadius: 12,
                cursor: loading || !name.trim() || !location.trim() ? "not-allowed" : "pointer",
                letterSpacing: "-0.02em", transition: "background 0.15s",
                display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
              }}
            >
              {loading && (
                <svg className="animate-spin" style={{ width: 16, height: 16 }} viewBox="0 0 24 24" fill="none">
                  <circle style={{ opacity: 0.25 }} cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                  <path style={{ opacity: 0.75 }} fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              )}
              {loading
                ? (mode === "ai" ? "Claude is writing…" : "Building site…")
                : `Generate ${mode === "ai" ? "AI-powered" : "template"} site`}
            </motion.button>
          </form>
        </motion.div>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              style={{
                background: "rgba(239,68,68,0.1)",
                border: "1px solid rgba(239,68,68,0.25)",
                color: "#f87171",
                fontSize: 13, fontWeight: 500,
                padding: "12px 16px", borderRadius: 12, marginBottom: 16,
              }}
            >
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Loading / Results */}
        <AnimatePresence mode="wait">
          {loading && <LoadingCard key="loading" mode={mode} step={step} />}
          {result && !loading && (
            <ResultCard
              key="result"
              result={result}
              onSaveToCrm={handleSaveToCrm}
              savedToCrm={savedToCrm}
            />
          )}
        </AnimatePresence>

        {/* Reset */}
        {result && !loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            style={{ textAlign: "center", marginTop: 24 }}
          >
            <button
              onClick={() => { setResult(null); setName(""); setLocation(""); setSavedToCrm(false); }}
              style={{ fontSize: 13, color: t.muted, background: "none", border: "none", cursor: "pointer" }}
            >
              Generate another →
            </button>
          </motion.div>
        )}
      </main>
    </PageWrapper>
    </ThemeProvider>
  );
}
