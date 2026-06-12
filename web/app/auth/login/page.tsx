"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { supabase } from "@/lib/supabase";
import { ease } from "@/components/ui/motion";
import { TBIcon } from "@/components/ui/logo";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Login page is always dark — set preference if user hasn't chosen one yet
  useEffect(() => {
    if (!localStorage.getItem("tb-theme")) {
      localStorage.setItem("tb-theme", "dark");
    }
  }, []);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const { error: authError } = await supabase.auth.signInWithPassword({ email, password });

      if (authError) {
        if (authError.message.includes("fetch") || authError.message.includes("Load failed") || authError.message.includes("network")) {
          router.push("/welcome");
          return;
        }
        setError(authError.message);
        setLoading(false);
        return;
      }
    } catch {
      router.push("/welcome");
      return;
    }

    router.push("/welcome");
  }

  return (
    <div style={{ minHeight: "100vh", background: "#0A0A0B", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      {/* Background glow */}
      <div style={{
        position: "fixed", top: "30%", left: "50%", transform: "translate(-50%, -50%)",
        width: 500, height: 500, borderRadius: "50%",
        background: "radial-gradient(circle, rgba(249,115,22,0.08) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: ease.smooth }}
        style={{ width: "100%", maxWidth: 400 }}
      >
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 40, justifyContent: "center" }}>
          <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 8 }}>
            <TBIcon size={22} />
            <span style={{ fontWeight: 900, fontSize: 18, letterSpacing: "-0.04em", color: "#f4f4f5" }}>TradeBuilt</span>
          </Link>
        </div>

        <div style={{
          background: "#111113",
          border: "1px solid rgba(255,255,255,0.07)",
          borderRadius: 18,
          padding: 32,
        }}>
          <h1 style={{ fontSize: 22, fontWeight: 900, color: "#f4f4f5", letterSpacing: "-0.04em", marginBottom: 6, textAlign: "center" }}>
            Sign in
          </h1>
          <p style={{ fontSize: 13, color: "#52525b", textAlign: "center", marginBottom: 28 }}>
            Welcome back. Let&apos;s close some clients.
          </p>

          <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {[
              { label: "Email", type: "email", value: email, onChange: (v: string) => setEmail(v), placeholder: "you@example.com" },
              { label: "Password", type: "password", value: password, onChange: (v: string) => setPassword(v), placeholder: "••••••••" },
            ].map((f) => (
              <div key={f.label}>
                <label style={{ display: "block", fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "#52525b", marginBottom: 8 }}>
                  {f.label}
                </label>
                <input
                  type={f.type}
                  value={f.value}
                  onChange={(e) => f.onChange(e.target.value)}
                  placeholder={f.placeholder}
                  required
                  disabled={loading}
                  style={{
                    width: "100%", boxSizing: "border-box",
                    background: "rgba(255,255,255,0.03)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: 10, padding: "11px 14px",
                    fontSize: 14, color: "#e4e4e7", outline: "none",
                    transition: "border-color 0.15s",
                  }}
                  onFocus={(e) => { e.target.style.borderColor = "rgba(249,115,22,0.4)"; }}
                  onBlur={(e) => { e.target.style.borderColor = "rgba(255,255,255,0.08)"; }}
                />
              </div>
            ))}

            {error && (
              <div style={{
                background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)",
                color: "#f87171", fontSize: 12, fontWeight: 500,
                padding: "10px 14px", borderRadius: 10,
              }}>
                {error}
              </div>
            )}

            <motion.button
              type="submit"
              whileHover={!loading ? { scale: 1.01, boxShadow: "0 0 28px rgba(249,115,22,0.35)" } : {}}
              whileTap={{ scale: 0.98 }}
              disabled={loading}
              style={{
                width: "100%", padding: "13px 0",
                background: loading ? "rgba(249,115,22,0.3)" : "#f97316",
                color: "#fff", fontSize: 14, fontWeight: 800,
                border: "none", borderRadius: 10,
                cursor: loading ? "not-allowed" : "pointer",
                letterSpacing: "-0.01em", marginTop: 4,
                display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
              }}
            >
              {loading && (
                <svg className="animate-spin" style={{ width: 14, height: 14 }} viewBox="0 0 24 24" fill="none">
                  <circle style={{ opacity: 0.25 }} cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                  <path style={{ opacity: 0.75 }} fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              )}
              {loading ? "Signing in…" : "Sign in"}
            </motion.button>
          </form>
        </div>

        <p style={{ textAlign: "center", fontSize: 13, color: "#52525b", marginTop: 20 }}>
          No account?{" "}
          <Link href="/auth/signup" style={{ color: "#f97316", fontWeight: 600, textDecoration: "none" }}>
            Sign up free
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
