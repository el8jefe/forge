"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { PageWrapper } from "@/components/ui/motion";
import { TBIcon } from "@/components/ui/logo";
import { ThemeProvider, ThemeToggle, useT } from "@/lib/theme";
import { useAuthGuard } from "@/lib/auth";
import { authFetch } from "@/lib/fetch-auth";
import type { ForgeJob } from "@/lib/forge-client";

type ForgeStats = {
  total: number;
  by_status: Record<string, number>;
  by_tier: Record<string, number>;
};

function AdminContent() {
  const t = useT();
  const [stats, setStats] = useState<ForgeStats | null>(null);
  const [jobs, setJobs] = useState<ForgeJob[]>([]);
  const [health, setHealth] = useState<string>("checking…");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const [statsRes, jobsRes, healthRes] = await Promise.all([
        authFetch("/api/forge/stats"),
        authFetch("/api/forge/jobs/list?limit=15"),
        authFetch("/api/forge/health"),
      ]);
      if (statsRes.status === 403) {
        setError("Access denied — your account is not authorized for pipeline admin.");
        return;
      }
      if (statsRes.ok) setStats(await statsRes.json());
      if (jobsRes.ok) {
        const data = await jobsRes.json();
        setJobs(data.jobs ?? []);
      }
      if (healthRes.ok) {
        const h = await healthRes.json();
        setHealth(`v${h.version} · ${h.storage} · celery=${h.celery}`);
      } else {
        setHealth("unreachable");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load admin data");
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 8000);
    return () => clearInterval(id);
  }, [refresh]);

  async function trigger(path: string, label: string) {
    setBusy(label);
    setError(null);
    try {
      const res = await authFetch(path, { method: "POST" });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error((body as { error?: string }).error ?? `HTTP ${res.status}`);
      }
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <PageWrapper>
      <nav style={{
        borderBottom: `1px solid ${t.border}`,
        background: t.navBg,
        position: "sticky", top: 0, zIndex: 40,
      }}>
        <div style={{ maxWidth: 960, margin: "0 auto", padding: "0 24px", height: 64, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 8 }}>
            <TBIcon size={20} />
            <span style={{ fontWeight: 900, fontSize: 16, color: t.text }}>FORGE Admin</span>
          </Link>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <ThemeToggle />
            <Link href="/dashboard" style={{ fontSize: 13, color: t.muted, textDecoration: "none" }}>CRM →</Link>
            <Link href="/generate" style={{ fontSize: 13, color: t.muted, textDecoration: "none" }}>Generate →</Link>
          </div>
        </div>
      </nav>

      <main style={{ maxWidth: 960, margin: "0 auto", padding: "40px 24px 80px" }}>
        <h1 style={{ fontSize: 28, fontWeight: 900, color: t.text, letterSpacing: "-0.03em", marginBottom: 8 }}>
          Pipeline operations
        </h1>
        <p style={{ color: t.muted, fontSize: 14, marginBottom: 32 }}>
          Engine health: {health}
        </p>

        {error && (
          <div style={{
            background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)",
            color: "#f87171", padding: "12px 16px", borderRadius: 10, marginBottom: 24, fontSize: 13,
          }}>
            {error}
          </div>
        )}

        {stats && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 12, marginBottom: 32 }}>
            <Stat label="Total leads" value={stats.total} t={t} />
            {Object.entries(stats.by_tier).slice(0, 4).map(([k, v]) => (
              <Stat key={k} label={k} value={v} t={t} />
            ))}
          </div>
        )}

        <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 40 }}>
          <ActionButton t={t} disabled={!!busy} onClick={() => trigger("/api/forge/run-pipeline", "pipeline")}>
            {busy === "pipeline" ? "Starting…" : "Run full pipeline"}
          </ActionButton>
          <ActionButton t={t} disabled={!!busy} onClick={() => trigger("/api/forge/scrape", "scrape")}>
            {busy === "scrape" ? "Starting…" : "Scrape leads"}
          </ActionButton>
          <ActionButton t={t} disabled={!!busy} onClick={() => trigger("/api/forge/run-agent", "agent")}>
            {busy === "agent" ? "Starting…" : "Run agent"}
          </ActionButton>
        </div>

        <h2 style={{ fontSize: 13, fontWeight: 800, letterSpacing: "0.08em", textTransform: "uppercase", color: t.muted, marginBottom: 16 }}>
          Recent jobs
        </h2>
        <div style={{ background: t.card, border: `1px solid ${t.border}`, borderRadius: 12, overflow: "hidden" }}>
          {jobs.length === 0 ? (
            <p style={{ padding: 20, color: t.muted, fontSize: 13 }}>No jobs yet.</p>
          ) : (
            jobs.map((job) => (
              <div
                key={job.id}
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr auto auto",
                  gap: 12,
                  padding: "14px 18px",
                  borderBottom: `1px solid ${t.subtleBorder}`,
                  fontSize: 13,
                  alignItems: "center",
                }}
              >
                <div>
                  <span style={{ fontWeight: 700, color: t.text }}>{job.type}</span>
                  <span style={{ color: t.muted, marginLeft: 8, fontFamily: "monospace", fontSize: 11 }}>
                    {job.id.slice(0, 8)}
                  </span>
                </div>
                <StatusBadge status={job.status} />
                <span style={{ color: t.muted, fontSize: 11 }}>
                  {job.leads_found ?? job.sites_built ?? job.emails_sent ?? "—"}
                </span>
              </div>
            ))
          )}
        </div>
      </main>
    </PageWrapper>
  );
}

function Stat({ label, value, t }: { label: string; value: number; t: ReturnType<typeof useT> }) {
  return (
    <div style={{ background: t.card, border: `1px solid ${t.border}`, borderRadius: 10, padding: "14px 16px" }}>
      <div style={{ fontSize: 22, fontWeight: 900, color: t.text }}>{value}</div>
      <div style={{ fontSize: 11, color: t.muted, marginTop: 4 }}>{label}</div>
    </div>
  );
}

function ActionButton({
  children, onClick, disabled, t,
}: {
  children: React.ReactNode;
  onClick: () => void;
  disabled: boolean;
  t: ReturnType<typeof useT>;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      style={{
        background: disabled ? "rgba(249,115,22,0.3)" : "#f97316",
        color: "#fff",
        border: "none",
        borderRadius: 10,
        padding: "10px 18px",
        fontSize: 13,
        fontWeight: 700,
        cursor: disabled ? "not-allowed" : "pointer",
      }}
    >
      {children}
    </button>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, { bg: string; text: string }> = {
    complete: { bg: "rgba(34,197,94,0.15)", text: "#4ade80" },
    running: { bg: "rgba(59,130,246,0.15)", text: "#60a5fa" },
    failed: { bg: "rgba(239,68,68,0.15)", text: "#f87171" },
    pending: { bg: "rgba(113,113,122,0.15)", text: "#a1a1aa" },
  };
  const c = colors[status] ?? colors.pending;
  return (
    <span style={{
      fontSize: 10, fontWeight: 800, letterSpacing: "0.06em", textTransform: "uppercase",
      padding: "4px 8px", borderRadius: 99, background: c.bg, color: c.text,
    }}>
      {status}
    </span>
  );
}

export default function AdminPage() {
  const checking = useAuthGuard();
  if (checking) return null;
  return (
    <ThemeProvider>
      <AdminContent />
    </ThemeProvider>
  );
}