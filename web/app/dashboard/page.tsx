"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { PageWrapper, ease } from "@/components/ui/motion";
import { TBIcon } from "@/components/ui/logo";
import type { LeadRecord, LeadStatus } from "@/lib/types";
import {
  getLeads,
  updateLeadStatus,
  updateLeadNotes,
  deleteLead,
  getStats,
  type CrmStats,
} from "@/lib/crm";
import { ThemeProvider, ThemeToggle, useT } from "@/lib/theme";
import { useAuthGuard } from "@/lib/auth";
import { authFetch } from "@/lib/fetch-auth";

// ── Types ─────────────────────────────────────────────────────────────────────
type Tab = "all" | LeadStatus;

// ── Config ────────────────────────────────────────────────────────────────────
const STATUS_LABEL: Record<LeadStatus, string> = {
  not_contacted: "Not contacted",
  emailed:       "Emailed",
  called:        "Called",
  responded:     "Responded",
  won:           "Won",
  lost:          "Lost",
};

const STATUS_COLORS: Record<LeadStatus, { bg: string; text: string }> = {
  not_contacted: { bg: "rgba(113,113,122,0.15)", text: "#a1a1aa" },
  emailed:       { bg: "rgba(139,92,246,0.15)",  text: "#a78bfa" },
  called:        { bg: "rgba(245,158,11,0.15)",  text: "#fbbf24" },
  responded:     { bg: "rgba(249,115,22,0.15)",  text: "#fb923c" },
  won:           { bg: "rgba(34,197,94,0.15)",   text: "#4ade80" },
  lost:          { bg: "rgba(239,68,68,0.15)",   text: "#f87171" },
};

const TEMP_COLORS: Record<string, { bg: string; text: string; dot: string; label: string }> = {
  burning: { bg: "rgba(239,68,68,0.12)",    text: "#f87171", dot: "#ef4444", label: "Burning Hot" },
  hot:     { bg: "rgba(249,115,22,0.12)",   text: "#fb923c", dot: "#f97316", label: "Hot" },
  warm:    { bg: "rgba(245,158,11,0.12)",   text: "#fbbf24", dot: "#f59e0b", label: "Warm" },
  cold:    { bg: "rgba(113,113,122,0.12)",  text: "#a1a1aa", dot: "#71717a", label: "Cold" },
};

// ── Stat card ─────────────────────────────────────────────────────────────────
function StatCard({ label, value, accent = false }: { label: string; value: number; accent?: boolean }) {
  const t = useT();
  return (
    <motion.div
      whileHover={{ y: -2 }}
      transition={{ type: "spring", stiffness: 300, damping: 24 }}
      style={{
        background: t.card,
        border: `1px solid ${accent ? "rgba(249,115,22,0.2)" : t.border}`,
        borderRadius: 12,
        padding: "16px 20px",
        ...(accent ? { boxShadow: "0 0 20px rgba(249,115,22,0.08)" } : {}),
      }}
    >
      <div style={{ fontSize: 28, fontWeight: 900, color: accent ? t.orange : t.text, letterSpacing: "-0.04em", lineHeight: 1 }}>
        {value}
      </div>
      <div style={{ fontSize: 11, color: t.muted, fontWeight: 600, marginTop: 4, letterSpacing: "0.04em" }}>{label}</div>
    </motion.div>
  );
}

// ── Lead card ─────────────────────────────────────────────────────────────────
function LeadCard({ lead, onRefresh }: { lead: LeadRecord; onRefresh: () => void }) {
  const t = useT();
  const [expanded, setExpanded] = useState(false);
  const [editingNotes, setEditingNotes] = useState(false);
  const [noteText, setNoteText] = useState(lead.notes ?? "");
  const [sendingEmail, setSendingEmail] = useState(false);
  const [emailResult, setEmailResult] = useState<"sent" | "error" | null>(null);

  const tempConf = lead.lead_quality
    ? TEMP_COLORS[lead.lead_quality.temperature_short] ?? TEMP_COLORS.cold
    : null;

  const statusConf = STATUS_COLORS[lead.status];

  // Job number from ID (last 6 chars, uppercase)
  const jobNum = `#${lead.id.slice(-6).toUpperCase()}`;

  async function handleSendEmail() {
    if (!lead.business.email || !lead.demo_url) return;
    setSendingEmail(true);
    try {
      const res = await authFetch("/api/send-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to_email: lead.business.email,
          to_name: lead.business.name,
          business_name: lead.business.name,
          demo_url: lead.demo_url,
          service_type: lead.business.service_type,
          city: lead.business.city,
        }),
      });
      setEmailResult(res.ok ? "sent" : "error");
      if (res.ok) {
        updateLeadStatus(lead.id, "emailed").then(onRefresh).catch(console.error);
      }
    } catch {
      setEmailResult("error");
    } finally {
      setSendingEmail(false);
    }
  }

  function handleStatusChange(status: LeadStatus) {
    updateLeadStatus(lead.id, status).then(onRefresh).catch(console.error);
  }

  function handleNoteSave() {
    updateLeadNotes(lead.id, noteText)
      .then(() => { setEditingNotes(false); onRefresh(); })
      .catch(console.error);
  }

  function handleDelete() {
    if (!confirm("Delete this lead?")) return;
    deleteLead(lead.id).then(onRefresh).catch(console.error);
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6, scale: 0.98 }}
      transition={{ duration: 0.3, ease: ease.smooth }}
      style={{
        background: t.card,
        border: `1px solid ${t.border}`,
        borderRadius: 14,
        overflow: "hidden",
        fontFamily: "inherit",
      }}
    >
      {/* Top accent line for burning hot */}
      {lead.lead_quality?.temperature_short === "burning" && (
        <div style={{ height: 2, background: "linear-gradient(90deg, #ef4444, #f97316)", flexShrink: 0 }} />
      )}

      {/* Main row */}
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "flex-start", gap: 16 }}>
        {/* Left: job number */}
        <div style={{
          flexShrink: 0,
          fontFamily: "'Courier New', monospace",
          fontSize: 10, fontWeight: 900,
          color: t.dim, letterSpacing: "0.08em",
          paddingTop: 2,
        }}>
          {jobNum}
        </div>

        {/* Center: info */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 4 }}>
            <h3 style={{ fontWeight: 800, color: t.text, fontSize: 15, letterSpacing: "-0.02em", margin: 0 }}>
              {lead.business.name}
            </h3>
            <span style={{
              fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase",
              background: t.tabBg, color: t.muted,
              padding: "2px 8px", borderRadius: 99,
            }}>
              {lead.business.service_type}
            </span>
          </div>
          <p style={{ fontSize: 12, color: t.muted, margin: 0, marginBottom: 6 }}>
            {lead.business.city}{lead.business.state ? `, ${lead.business.state}` : ""}
            {lead.business.phone && <span style={{ marginLeft: 12, fontFamily: "monospace" }}>{lead.business.phone}</span>}
            {lead.business.email && <span style={{ marginLeft: 12 }}>{lead.business.email}</span>}
          </p>
          {lead.lead_quality && (
            <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
              {tempConf && (
                <span style={{
                  display: "inline-flex", alignItems: "center", gap: 5,
                  background: tempConf.bg, color: tempConf.text,
                  fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase",
                  padding: "3px 8px", borderRadius: 99,
                }}>
                  <span style={{ width: 4, height: 4, borderRadius: "50%", background: tempConf.dot, display: "block" }} />
                  {tempConf.label}
                </span>
              )}
              <span style={{ fontSize: 11, color: t.muted }}>{lead.lead_quality.reason}</span>
            </div>
          )}
          {lead.notes && (
            <div style={{
              marginTop: 8, fontSize: 11, color: t.body,
              background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.15)",
              padding: "6px 10px", borderRadius: 8,
            }}>
              {lead.notes}
            </div>
          )}
        </div>

        {/* Right: score + status */}
        <div style={{ flexShrink: 0, textAlign: "right", display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8 }}>
          {lead.score && (
            <div>
              <span style={{ fontSize: 22, fontWeight: 900, color: t.text, letterSpacing: "-0.04em" }}>
                {lead.score.score.toFixed(1)}
              </span>
              <span style={{ fontSize: 10, color: t.muted }}>/10</span>
            </div>
          )}
          <span style={{
            fontSize: 10, fontWeight: 800, letterSpacing: "0.1em", textTransform: "uppercase",
            background: statusConf.bg, color: statusConf.text,
            padding: "3px 10px", borderRadius: 99,
            fontFamily: "'Courier New', monospace",
          }}>
            {STATUS_LABEL[lead.status]}
          </span>
        </div>
      </div>

      {/* Action bar */}
      <div style={{
        borderTop: `1px solid ${t.subtleBorder}`,
        padding: "10px 20px",
        display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap",
        background: t.cardAlt,
      }}>
        <select
          value={lead.status}
          onChange={(e) => handleStatusChange(e.target.value as LeadStatus)}
          style={{
            fontSize: 11, fontWeight: 700, letterSpacing: "0.04em",
            background: t.tabBg, border: `1px solid ${t.border}`,
            borderRadius: 7, padding: "6px 10px",
            color: t.body, outline: "none", cursor: "pointer",
          }}
        >
          {Object.entries(STATUS_LABEL).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>

        {lead.demo_url && (
          <a
            href={lead.demo_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{ fontSize: 12, fontWeight: 600, color: "#3b82f6", textDecoration: "none" }}
          >
            View demo ↗
          </a>
        )}

        {lead.business.email && lead.demo_url && (
          <button
            onClick={handleSendEmail}
            disabled={sendingEmail || lead.status === "emailed"}
            style={{
              fontSize: 11, fontWeight: 700,
              padding: "6px 12px", borderRadius: 7, cursor: "pointer",
              border: "none", transition: "all 0.15s",
              opacity: (sendingEmail || lead.status === "emailed") ? 0.4 : 1,
              ...(emailResult === "sent"
                ? { background: "rgba(34,197,94,0.12)", color: "#4ade80" }
                : emailResult === "error"
                ? { background: "rgba(239,68,68,0.12)", color: "#f87171" }
                : { background: "rgba(249,115,22,0.12)", color: "#fb923c" }),
            }}
          >
            {sendingEmail ? "Sending…" :
              emailResult === "sent" ? "✓ Sent" :
              emailResult === "error" ? "✗ Failed" :
              "Send email"}
          </button>
        )}

        <div style={{ display: "flex", alignItems: "center", gap: 12, marginLeft: "auto" }}>
          <button
            onClick={() => setExpanded(!expanded)}
            style={{ fontSize: 12, color: t.muted, background: "none", border: "none", cursor: "pointer", fontWeight: 600 }}
          >
            {expanded ? "Less" : "Details"}
          </button>
          <button
            onClick={handleDelete}
            style={{ fontSize: 12, color: t.dim, background: "none", border: "none", cursor: "pointer" }}
          >
            Remove
          </button>
        </div>
      </div>

      {/* Expanded */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: ease.smooth }}
            style={{ overflow: "hidden" }}
          >
            <div style={{ borderTop: `1px solid ${t.subtleBorder}`, padding: "16px 20px" }}>
              {/* Score bars */}
              {lead.score && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px 28px", marginBottom: 16 }}>
                  {Object.entries(lead.score.breakdown).map(([dim, val]) => (
                    <div key={dim}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
                        <span style={{ fontSize: 10, color: t.muted, textTransform: "capitalize", letterSpacing: "0.04em" }}>{dim}</span>
                        <span style={{ fontSize: 11, fontWeight: 700, color: t.body }}>{(val as number).toFixed(0)}/10</span>
                      </div>
                      <div style={{ height: 2, background: t.subtleBorder, borderRadius: 99, overflow: "hidden" }}>
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${((val as number) / 10) * 100}%` }}
                          transition={{ duration: 0.5, ease: ease.smooth }}
                          style={{ height: "100%", borderRadius: 99, background: "#f97316" }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Notes */}
              {editingNotes ? (
                <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                  <textarea
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    placeholder="Add a note…"
                    rows={2}
                    autoFocus
                    style={{
                      flex: 1, fontSize: 12,
                      background: t.tabBg, border: `1px solid ${t.border}`,
                      borderRadius: 8, padding: "8px 12px",
                      color: t.text, resize: "none", outline: "none",
                    }}
                  />
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    <button
                      onClick={handleNoteSave}
                      style={{
                        fontSize: 11, fontWeight: 700,
                        background: "#f97316", color: "#fff",
                        border: "none", borderRadius: 7, padding: "6px 12px", cursor: "pointer",
                      }}
                    >Save</button>
                    <button
                      onClick={() => setEditingNotes(false)}
                      style={{ fontSize: 11, color: t.muted, background: "none", border: "none", cursor: "pointer" }}
                    >Cancel</button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => { setEditingNotes(true); setNoteText(lead.notes ?? ""); }}
                  style={{ fontSize: 12, color: t.muted, background: "none", border: "none", cursor: "pointer", fontWeight: 600 }}
                >
                  {lead.notes ? "Edit note" : "+ Add note"}
                </button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const checking = useAuthGuard();
  const t = useT();
  const [leads, setLeads] = useState<LeadRecord[]>([]);
  const [stats, setStats] = useState<CrmStats | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("all");

  const reload = useCallback(() => {
    getLeads().then(setLeads).catch((err) => console.error("getLeads failed:", err?.message ?? err));
    getStats().then(setStats).catch((err) => console.error("getStats failed:", err?.message ?? err));
  }, []);

  useEffect(() => { reload(); }, [reload]);

  const filtered = activeTab === "all"
    ? leads
    : leads.filter((l) => l.status === activeTab);

  const tabs: Array<{ key: Tab; label: string; count: number }> = [
    { key: "all",           label: "All",          count: stats?.total         ?? 0 },
    { key: "not_contacted", label: "Not contacted", count: stats?.not_contacted ?? 0 },
    { key: "emailed",       label: "Emailed",       count: stats?.emailed       ?? 0 },
    { key: "called",        label: "Called",        count: stats?.called        ?? 0 },
    { key: "responded",     label: "Responded",     count: stats?.responded     ?? 0 },
    { key: "won",           label: "Won",           count: stats?.won           ?? 0 },
  ];

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
        <div style={{ maxWidth: 1000, margin: "0 auto", padding: "0 24px", height: 64, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Link href="/" style={{ textDecoration: "none" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <TBIcon size={20} />
              <span style={{ fontWeight: 900, fontSize: 16, letterSpacing: "-0.04em", color: t.text }}>TradeBuilt</span>
            </div>
          </Link>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <ThemeToggle />
            <Link href="/generate">
              <motion.span
                whileHover={{ scale: 1.03, boxShadow: "0 0 20px rgba(249,115,22,0.3)" }}
                whileTap={{ scale: 0.97 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
                style={{
                  display: "inline-block",
                  background: "#f97316", color: "#fff",
                  fontSize: 13, fontWeight: 700,
                  padding: "8px 18px", borderRadius: 8,
                  letterSpacing: "-0.01em",
                }}
              >
                + New lead
              </motion.span>
            </Link>
          </div>
        </div>
      </nav>

      <main style={{ maxWidth: 1000, margin: "0 auto", padding: "40px 24px 80px" }}>
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: ease.smooth }}
          style={{ marginBottom: 32 }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
            <h1 style={{ fontSize: 28, fontWeight: 900, color: t.text, letterSpacing: "-0.04em", margin: 0 }}>
              Lead pipeline
            </h1>
            {stats && stats.total > 0 && (
              <span style={{
                fontSize: 11, fontWeight: 800, letterSpacing: "0.08em",
                background: t.tabBg, color: t.muted,
                padding: "3px 10px", borderRadius: 99,
                fontFamily: "'Courier New', monospace",
              }}>
                {stats.total} total
              </span>
            )}
          </div>
          <p style={{ color: t.muted, fontSize: 13 }}>
            Track and manage every business you&apos;ve pitched.
          </p>
        </motion.div>

        {/* Stats */}
        {stats && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.08, ease: ease.smooth }}
            style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 28 }}
          >
            <StatCard label="Burning Hot" value={stats.burning} accent />
            <StatCard label="Hot leads"   value={stats.hot} />
            <StatCard label="Deals won"   value={stats.won} />
            <StatCard label="Total leads" value={stats.total} />
          </motion.div>
        )}

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.15 }}
          style={{
            display: "flex", gap: 4, padding: 4,
            background: t.tabBg,
            border: `1px solid ${t.border}`,
            borderRadius: 12, marginBottom: 20,
            overflowX: "auto",
          }}
        >
          {tabs.map((tab) => (
            <motion.button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              whileTap={{ scale: 0.97 }}
              style={{
                position: "relative",
                display: "flex", alignItems: "center", gap: 6,
                padding: "7px 14px", borderRadius: 8, border: "none",
                fontSize: 12, fontWeight: 700, whiteSpace: "nowrap", cursor: "pointer",
                background: activeTab === tab.key ? t.tabActive : "transparent",
                color: activeTab === tab.key ? t.text : t.muted,
                transition: "all 0.15s",
                boxShadow: activeTab === tab.key ? "0 1px 4px rgba(0,0,0,0.3)" : "none",
              }}
            >
              {activeTab === tab.key && (
                <motion.div
                  layoutId="tab-indicator"
                  style={{ position: "absolute", inset: 0, background: t.tabActive, borderRadius: 8 }}
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
              <span style={{ position: "relative" }}>{tab.label}</span>
              {tab.count > 0 && (
                <span style={{
                  position: "relative",
                  fontSize: 10, fontWeight: 800,
                  background: activeTab === tab.key ? "rgba(249,115,22,0.15)" : t.tabBg,
                  color: activeTab === tab.key ? t.orange : t.muted,
                  padding: "1px 6px", borderRadius: 99,
                  fontFamily: "monospace",
                }}>
                  {tab.count}
                </span>
              )}
            </motion.button>
          ))}
        </motion.div>

        {/* Lead list */}
        <AnimatePresence mode="popLayout">
          {filtered.length === 0 ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              style={{ textAlign: "center", paddingTop: 80, paddingBottom: 80 }}
            >
              <div style={{
                width: 52, height: 52, borderRadius: 12, margin: "0 auto 16px",
                display: "flex", alignItems: "center", justifyContent: "center",
                background: "rgba(249,115,22,0.08)", border: "1px solid rgba(249,115,22,0.12)",
              }}>
                <svg style={{ width: 22, height: 22, color: t.muted }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/>
                  <rect x="9" y="3" width="6" height="4" rx="1"/>
                </svg>
              </div>
              <p style={{ color: t.body, fontWeight: 700, fontSize: 15, marginBottom: 6 }}>No leads here yet</p>
              <p style={{ color: t.muted, fontSize: 13, marginBottom: 24 }}>
                Generate a demo site and save it to your pipeline.
              </p>
              <Link href="/generate">
                <motion.span
                  whileHover={{ scale: 1.02, boxShadow: "0 0 20px rgba(249,115,22,0.3)" }}
                  whileTap={{ scale: 0.97 }}
                  style={{
                    display: "inline-flex", alignItems: "center", gap: 8,
                    background: "#f97316", color: "#fff",
                    fontSize: 13, fontWeight: 700,
                    padding: "10px 20px", borderRadius: 10, cursor: "pointer",
                  }}
                >
                  Generate first lead →
                </motion.span>
              </Link>
            </motion.div>
          ) : (
            <motion.div key="list" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <AnimatePresence mode="popLayout">
                {filtered.map((lead) => (
                  <LeadCard key={lead.id} lead={lead} onRefresh={reload} />
                ))}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </PageWrapper>
    </ThemeProvider>
  );
}
