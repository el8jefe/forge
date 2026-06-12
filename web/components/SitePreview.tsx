"use client";

import type { GeneratedContent, NormalizedBusiness } from "@/lib/types";

interface Props {
  content: GeneratedContent;
  business: NormalizedBusiness;
}

// Trade-type to gradient mapping — purely visual, no logic locked in
const ACCENT_COLORS: Record<string, string> = {
  HVAC: "#f97316",
  Plumbing: "#3b82f6",
  Electrical: "#eab308",
  Roofing: "#ef4444",
  Landscaping: "#22c55e",
  "Pest Control": "#a855f7",
  Painting: "#ec4899",
  Cleaning: "#06b6d4",
};

function getAccent(serviceType: string): string {
  for (const [key, color] of Object.entries(ACCENT_COLORS)) {
    if (serviceType.toLowerCase().includes(key.toLowerCase())) return color;
  }
  return "#f97316"; // default orange
}

export default function SitePreview({ content, business }: Props) {
  const accent = getAccent(business.service_type);

  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
      {/* Browser chrome */}
      <div className="bg-white/5 border-b border-white/10 px-4 py-2.5 flex items-center gap-2">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500/50" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
          <div className="w-3 h-3 rounded-full bg-green-500/50" />
        </div>
        <div className="flex-1 mx-3 bg-white/5 rounded-md px-3 py-0.5 text-xs text-slate-500 font-mono">
          {business.name.toLowerCase().replace(/\s+/g, "-")}.com
        </div>
        <span className="text-xs text-slate-600">Preview</span>
      </div>

      {/* Website preview */}
      <div className="overflow-y-auto max-h-[600px] text-white">
        {/* Nav */}
        <div
          className="sticky top-0 z-10 flex items-center justify-between px-6 py-3 text-sm font-medium backdrop-blur-sm"
          style={{ background: `${accent}18`, borderBottom: `1px solid ${accent}25` }}
        >
          <span className="font-bold text-base">{business.name}</span>
          {business.phone && (
            <span className="text-slate-300">{business.phone}</span>
          )}
        </div>

        {/* Hero */}
        <div
          className="relative px-6 py-10 text-center"
          style={{
            background: `linear-gradient(135deg, #0a0f1e 0%, #111827 100%)`,
            borderBottom: `1px solid ${accent}20`,
          }}
        >
          <div
            className="absolute inset-0 opacity-20"
            style={{
              background: `radial-gradient(ellipse 70% 50% at 50% 0%, ${accent} 0%, transparent 70%)`,
            }}
          />
          <div className="relative">
            <h1 className="text-2xl md:text-3xl font-bold font-serif leading-tight mb-3">
              {content.hero}
            </h1>
            <p className="text-slate-300 text-sm leading-relaxed max-w-md mx-auto mb-5">
              {content.subheadline}
            </p>
            <button
              className="px-6 py-2.5 rounded-lg text-sm font-semibold text-white transition"
              style={{ background: accent }}
            >
              {content.cta}
            </button>
          </div>
        </div>

        {/* Services */}
        <div className="px-6 py-8 bg-[#0d1428]">
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-widest text-center mb-5">
            Our Services
          </h2>
          <div className="grid grid-cols-2 gap-3">
            {content.services.slice(0, 6).map((s, i) => (
              <div
                key={i}
                className="rounded-xl p-4 text-sm"
                style={{ background: `${accent}0d`, border: `1px solid ${accent}20` }}
              >
                <div className="text-xl mb-1.5">{s.icon}</div>
                <div className="font-semibold text-white mb-0.5">{s.name}</div>
                <div className="text-slate-400 text-xs leading-relaxed">
                  {s.description}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Trust Signals */}
        <div
          className="px-6 py-5 flex flex-wrap gap-2 justify-center"
          style={{ background: `${accent}08`, borderTop: `1px solid ${accent}15` }}
        >
          {content.trust_signals.map((t, i) => (
            <span
              key={i}
              className="text-xs px-3 py-1 rounded-full font-medium"
              style={{
                background: `${accent}15`,
                color: accent,
                border: `1px solid ${accent}30`,
              }}
            >
              ✓ {t}
            </span>
          ))}
        </div>

        {/* About */}
        <div className="px-6 py-8 bg-[#0a0f1e]">
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">
            About Us
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            {content.about_snippet}
          </p>
        </div>

        {/* CTA Footer */}
        <div
          className="px-6 py-6 text-center"
          style={{ background: `${accent}12`, borderTop: `1px solid ${accent}20` }}
        >
          <p className="text-white font-semibold text-sm mb-3">
            Ready to get started?
          </p>
          <button
            className="px-8 py-2.5 rounded-lg text-sm font-semibold text-white"
            style={{ background: accent }}
          >
            {content.cta}
          </button>
        </div>
      </div>
    </div>
  );
}
