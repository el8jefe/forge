"use client";

import { useState } from "react";
import type { GenerateSiteResponse } from "@/lib/types";
import ScoreCard from "./ScoreCard";
import SitePreview from "./SitePreview";

interface Props {
  result: GenerateSiteResponse;
  onReset: () => void;
}

export default function ResultsView({ result, onReset }: Props) {
  const [copied, setCopied] = useState(false);

  const { business, content, score } = result;

  async function copyHero() {
    await navigator.clipboard.writeText(content.hero);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="w-full animate-fade-in">
      {/* Header bar */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white">{business.name}</h2>
          <p className="text-slate-400 text-sm">
            {business.service_type} · {business.city}
            {business.state ? `, ${business.state}` : ""}
            {result.cached && (
              <span className="ml-2 text-xs bg-white/5 border border-white/10 rounded-full px-2 py-0.5">
                Cached
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={copyHero}
            className="text-sm px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10 transition"
          >
            {copied ? "Copied!" : "Copy Hero"}
          </button>
          <button
            onClick={onReset}
            className="text-sm px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10 transition"
          >
            New Search
          </button>
        </div>
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Site Preview — larger */}
        <div className="lg:col-span-3">
          <SitePreview content={content} business={business} />
        </div>

        {/* Score Card — sidebar */}
        <div className="lg:col-span-2">
          <ScoreCard score={score} />
        </div>
      </div>

      {/* Upsell Banner */}
      <div className="mt-6 rounded-2xl border border-orange-500/20 bg-orange-500/5 p-5 flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <p className="font-semibold text-white">
            Want this site deployed in 24 hours?
          </p>
          <p className="text-slate-400 text-sm mt-0.5">
            Upgrade to Pro — we build, host, and optimize your site for{" "}
            <strong className="text-white">$9.99/month</strong>.
          </p>
        </div>
        <button className="shrink-0 bg-orange-500 hover:bg-orange-600 text-white font-semibold px-5 py-2.5 rounded-xl transition text-sm">
          Upgrade to Pro →
        </button>
      </div>

      {/* Donation nudge */}
      <div className="mt-3 text-center text-sm text-slate-600">
        Enjoying the free tier?{" "}
        <button className="text-slate-400 underline underline-offset-2 hover:text-white transition">
          Buy us a coffee ☕
        </button>
      </div>
    </div>
  );
}
