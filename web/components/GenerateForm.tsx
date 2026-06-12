"use client";

import { useState } from "react";

interface Props {
  onSubmit: (name: string, location: string) => void;
  loading: boolean;
}

export default function GenerateForm({ onSubmit, loading }: Props) {
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !location.trim()) return;
    onSubmit(name.trim(), location.trim());
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-xl mx-auto">
      <div className="bg-white/5 border border-white/10 rounded-2xl p-6 md:p-8 backdrop-blur-sm">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1.5">
              Business Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Mike's Plumbing & Heating"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500/50 transition"
              disabled={loading}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1.5">
              Location
            </label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Denver, CO"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500/50 transition"
              disabled={loading}
              required
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !name.trim() || !location.trim()}
          className="mt-6 w-full bg-orange-500 hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3.5 rounded-xl transition-all hover:shadow-lg hover:shadow-orange-500/25 hover:-translate-y-0.5 active:translate-y-0"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              Generating…
            </span>
          ) : (
            "Generate My Website →"
          )}
        </button>

        <p className="mt-3 text-center text-xs text-slate-600">
          Free · No credit card · Powered by Claude AI
        </p>
      </div>
    </form>
  );
}
