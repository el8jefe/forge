"use client";

import { useContext, createContext, useState, useEffect } from "react";

// ── Token sets ────────────────────────────────────────────────────────────────

export const LIGHT = {
  bg:           "#FDF8F2",
  bg2:          "#F4EDE3",
  card:         "#FFFAF5",
  cardAlt:      "#F4EDE3",   // action bars, sunken rows
  text:         "#1C1208",
  body:         "#6B5E50",
  muted:        "#A89880",
  dim:          "#C8B8A8",   // monospace labels, lightest annotations
  border:       "rgba(120,80,30,0.10)",
  borderMed:    "rgba(120,80,30,0.16)",
  subtleBorder: "rgba(120,80,30,0.06)",
  tabBg:        "rgba(120,80,30,0.04)",
  tabActive:    "#fff",
  orange:       "#F97316",
  orangeGlow:   "0 8px 32px rgba(249,115,22,0.30)",
  shadow:       "0 1px 3px rgba(120,80,30,0.08), 0 4px 16px rgba(120,80,30,0.05)",
  shadowHover:  "0 4px 24px rgba(120,80,30,0.12), 0 1px 4px rgba(120,80,30,0.07)",
  navBg:        "rgba(253,252,251,0.88)",
  heroFade:     "rgba(253,248,242,0.85)",
  skeletonFrom: "#F4EDE3",
  skeletonTo:   "#EDE4D8",
  inputBg:      "#FDF8F2",
};

export const DARK = {
  bg:           "#0F0D0A",
  bg2:          "#13100D",
  card:         "#1C1712",
  cardAlt:      "#15120E",   // action bars, sunken rows
  text:         "#F0E6D6",
  body:         "#8A7868",
  muted:        "#5A4E44",
  dim:          "#332820",   // monospace labels, lightest annotations
  border:       "rgba(255,190,120,0.09)",
  borderMed:    "rgba(255,190,120,0.15)",
  subtleBorder: "rgba(255,190,120,0.05)",
  tabBg:        "rgba(255,190,120,0.04)",
  tabActive:    "#1C1712",
  orange:       "#F97316",
  orangeGlow:   "0 8px 32px rgba(249,115,22,0.40)",
  shadow:       "0 1px 3px rgba(0,0,0,0.40), 0 4px 16px rgba(0,0,0,0.30)",
  shadowHover:  "0 4px 24px rgba(0,0,0,0.50), 0 1px 4px rgba(0,0,0,0.40)",
  navBg:        "rgba(15,13,10,0.92)",
  heroFade:     "rgba(15,13,10,0.85)",
  skeletonFrom: "#1C1712",
  skeletonTo:   "#261F18",
  inputBg:      "#13100D",
};

export type Theme = typeof LIGHT;

// ── Context ───────────────────────────────────────────────────────────────────

export const ThemeCtx = createContext<{ t: Theme; dark: boolean; toggle: () => void }>({
  t: LIGHT, dark: false, toggle: () => {},
});

export function useT() { return useContext(ThemeCtx).t; }
export function useTheme() { return useContext(ThemeCtx); }

// ── Provider ──────────────────────────────────────────────────────────────────

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("tb-theme");
    if (saved === "dark") setDark(true);
  }, []);

  useEffect(() => {
    document.body.style.background = dark ? DARK.bg : LIGHT.bg;
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
    localStorage.setItem("tb-theme", dark ? "dark" : "light");
  }, [dark]);

  const toggle = () => setDark((d) => !d);
  const t = dark ? DARK : LIGHT;
  return <ThemeCtx.Provider value={{ t, dark, toggle }}>{children}</ThemeCtx.Provider>;
}

// ── Toggle button (shared across pages) ──────────────────────────────────────

import { motion } from "framer-motion";

export function ThemeToggle() {
  const { t, dark, toggle } = useTheme();
  return (
    <motion.button
      onClick={toggle}
      whileHover={{ scale: 1.08 }}
      whileTap={{ scale: 0.93 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      title={dark ? "Switch to light mode" : "Switch to night mode"}
      style={{
        display: "flex", alignItems: "center", justifyContent: "center",
        width: 36, height: 36, borderRadius: 10, cursor: "pointer", border: "none",
        background: dark ? "rgba(255,190,120,0.10)" : "rgba(120,80,30,0.08)",
        color: t.body, flexShrink: 0,
      }}
    >
      {dark ? (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="3.5" stroke="currentColor" strokeWidth="1.5"/>
          <path d="M8 1v1.5M8 13.5V15M1 8h1.5M13.5 8H15M2.93 2.93l1.06 1.06M12.01 12.01l1.06 1.06M2.93 13.07l1.06-1.06M12.01 3.99l1.06-1.06" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M13.5 9.5A6 6 0 016.5 2.5a6 6 0 100 11 6 6 0 007-4z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      )}
    </motion.button>
  );
}
