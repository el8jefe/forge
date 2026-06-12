/**
 * Trade-Specific Theme System
 * Each trade has a primary color, accent, gradient, and personality.
 */

export interface Theme {
  trade: string;
  primary: string;      // main brand color (buttons, accents)
  primaryDark: string;  // darker variant for hover
  accent: string;       // secondary accent
  bg: string;           // hero background
  bgDark: string;       // darker sections
  text: string;         // body text on light
  textLight: string;    // text on dark backgrounds
  gradient: string;     // CSS gradient for hero
  badgeBg: string;      // trust badge background
  emoji: string;        // trade emoji for display
  keywords: string[];   // used for detection
}

const themes: Record<string, Theme> = {
  hvac: {
    trade: "HVAC",
    primary: "#f97316",
    primaryDark: "#ea6c0a",
    accent: "#0d1b2a",
    bg: "#0d1b2a",
    bgDark: "#060e17",
    text: "#1e293b",
    textLight: "#f1f5f9",
    gradient: "linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 50%, #0f2940 100%)",
    badgeBg: "rgba(249,115,22,0.12)",
    emoji: "❄️",
    keywords: ["hvac", "heating", "cooling", "air conditioning", "ac", "furnace", "heat pump", "ductwork"],
  },
  plumbing: {
    trade: "Plumbing",
    primary: "#3b82f6",
    primaryDark: "#2563eb",
    accent: "#111827",
    bg: "#111827",
    bgDark: "#030712",
    text: "#1e293b",
    textLight: "#f1f5f9",
    gradient: "linear-gradient(135deg, #111827 0%, #1e3a5f 50%, #0f2040 100%)",
    badgeBg: "rgba(59,130,246,0.12)",
    emoji: "🔧",
    keywords: ["plumb", "pipe", "drain", "water heater", "leak", "sewer", "toilet", "faucet"],
  },
  electrical: {
    trade: "Electrical",
    primary: "#eab308",
    primaryDark: "#ca8a04",
    accent: "#0f172a",
    bg: "#0f172a",
    bgDark: "#020617",
    text: "#1e293b",
    textLight: "#f1f5f9",
    gradient: "linear-gradient(135deg, #0f172a 0%, #1e2d4d 50%, #0c1a30 100%)",
    badgeBg: "rgba(234,179,8,0.12)",
    emoji: "⚡",
    keywords: ["electric", "wiring", "panel", "outlet", "circuit", "electrician", "generator"],
  },
  roofing: {
    trade: "Roofing",
    primary: "#ef4444",
    primaryDark: "#dc2626",
    accent: "#1c1917",
    bg: "#1c1917",
    bgDark: "#0c0a09",
    text: "#1e293b",
    textLight: "#f1f5f9",
    gradient: "linear-gradient(135deg, #1c1917 0%, #3b1f1a 50%, #1a120f 100%)",
    badgeBg: "rgba(239,68,68,0.12)",
    emoji: "🏠",
    keywords: ["roof", "shingle", "gutter", "skylight", "flashing", "roofer"],
  },
  landscaping: {
    trade: "Landscaping",
    primary: "#22c55e",
    primaryDark: "#16a34a",
    accent: "#14532d",
    bg: "#14532d",
    bgDark: "#052e16",
    text: "#1e293b",
    textLight: "#f1f5f9",
    gradient: "linear-gradient(135deg, #14532d 0%, #1a6b38 50%, #0f3d22 100%)",
    badgeBg: "rgba(34,197,94,0.12)",
    emoji: "🌿",
    keywords: ["landscap", "lawn", "garden", "mow", "trim", "mulch", "irrigation", "hardscape"],
  },
  painting: {
    trade: "Painting",
    primary: "#a855f7",
    primaryDark: "#9333ea",
    accent: "#1e1b4b",
    bg: "#1e1b4b",
    bgDark: "#0f0d26",
    text: "#1e293b",
    textLight: "#f1f5f9",
    gradient: "linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1a1844 100%)",
    badgeBg: "rgba(168,85,247,0.12)",
    emoji: "🎨",
    keywords: ["paint", "stain", "epoxy", "drywall", "interior", "exterior paint"],
  },
  concrete: {
    trade: "Concrete",
    primary: "#64748b",
    primaryDark: "#475569",
    accent: "#0f172a",
    bg: "#1e293b",
    bgDark: "#0f172a",
    text: "#1e293b",
    textLight: "#f1f5f9",
    gradient: "linear-gradient(135deg, #1e293b 0%, #334155 50%, #1a2535 100%)",
    badgeBg: "rgba(100,116,139,0.12)",
    emoji: "🏗️",
    keywords: ["concrete", "cement", "driveway", "patio", "slab", "foundation"],
  },
  pest: {
    trade: "Pest Control",
    primary: "#10b981",
    primaryDark: "#059669",
    accent: "#064e3b",
    bg: "#064e3b",
    bgDark: "#022c22",
    text: "#1e293b",
    textLight: "#f1f5f9",
    gradient: "linear-gradient(135deg, #064e3b 0%, #065f46 50%, #022c22 100%)",
    badgeBg: "rgba(16,185,129,0.12)",
    emoji: "🐛",
    keywords: ["pest", "termite", "rodent", "bug", "insect", "exterminator", "fumigat"],
  },
  cleaning: {
    trade: "Cleaning",
    primary: "#06b6d4",
    primaryDark: "#0891b2",
    accent: "#083344",
    bg: "#083344",
    bgDark: "#021a25",
    text: "#1e293b",
    textLight: "#f1f5f9",
    gradient: "linear-gradient(135deg, #083344 0%, #0c4a6e 50%, #052433 100%)",
    badgeBg: "rgba(6,182,212,0.12)",
    emoji: "✨",
    keywords: ["clean", "maid", "janitorial", "pressure wash", "window clean", "carpet"],
  },
  default: {
    trade: "Home Services",
    primary: "#f97316",
    primaryDark: "#ea6c0a",
    accent: "#1e293b",
    bg: "#1e293b",
    bgDark: "#0f172a",
    text: "#1e293b",
    textLight: "#f1f5f9",
    gradient: "linear-gradient(135deg, #1e293b 0%, #2d3f55 50%, #162030 100%)",
    badgeBg: "rgba(249,115,22,0.12)",
    emoji: "🔨",
    keywords: [],
  },
};

export function getTheme(serviceType: string): Theme {
  const st = serviceType.toLowerCase();
  for (const [key, theme] of Object.entries(themes)) {
    if (key === "default") continue;
    if (theme.keywords.some((kw) => st.includes(kw))) return theme;
  }
  return themes.default;
}

export { themes };
export default themes;
