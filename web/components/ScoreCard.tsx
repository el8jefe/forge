"use client";

import type { ScoreResult } from "@/lib/types";

interface Props {
  score: ScoreResult;
}

const DIMENSIONS = [
  { key: "clarity" as const, label: "Clarity", desc: "How easy to understand" },
  { key: "specificity" as const, label: "Specificity", desc: "How localized & relevant" },
  { key: "trust" as const, label: "Trust", desc: "Credibility signals" },
  { key: "conversion" as const, label: "Conversion", desc: "CTA & urgency strength" },
];

function scoreColor(s: number) {
  if (s >= 8) return "text-emerald-400";
  if (s >= 6) return "text-yellow-400";
  return "text-red-400";
}

function barColor(s: number) {
  if (s >= 8) return "bg-emerald-500";
  if (s >= 6) return "bg-yellow-500";
  return "bg-red-500";
}

function scoreLabel(s: number) {
  if (s >= 9) return "Excellent";
  if (s >= 8) return "Great";
  if (s >= 7) return "Good";
  if (s >= 6) return "Fair";
  return "Needs Work";
}

export default function ScoreCard({ score }: Props) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 h-full">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <p className="text-sm font-medium text-slate-400 uppercase tracking-wider">
            Site Score
          </p>
          <div className="flex items-end gap-2 mt-1">
            <span className={`text-5xl font-bold font-serif ${scoreColor(score.score)}`}>
              {score.score.toFixed(1)}
            </span>
            <span className="text-slate-500 text-lg mb-1.5">/10</span>
          </div>
          <span className={`text-sm font-semibold ${scoreColor(score.score)}`}>
            {scoreLabel(score.score)}
          </span>
        </div>

        {/* Radial visual */}
        <div className="relative w-16 h-16">
          <svg className="w-16 h-16 -rotate-90" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="26" fill="none" stroke="white" strokeOpacity="0.06" strokeWidth="6" />
            <circle
              cx="32" cy="32" r="26"
              fill="none"
              stroke={score.score >= 8 ? "#10b981" : score.score >= 6 ? "#eab308" : "#ef4444"}
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={`${(score.score / 10) * 163.4} 163.4`}
              className="transition-all duration-1000"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center text-xl">
            {score.score >= 8 ? "🏆" : score.score >= 6 ? "⚡" : "🔧"}
          </div>
        </div>
      </div>

      {/* Feedback */}
      <p className="text-slate-300 text-sm mb-5 leading-relaxed">
        {score.feedback}
      </p>

      {/* Breakdown bars */}
      <div className="space-y-3 mb-5">
        {DIMENSIONS.map((dim) => {
          const val = score.breakdown[dim.key];
          return (
            <div key={dim.key}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-slate-300">
                  {dim.label}
                </span>
                <span className={`text-sm font-semibold tabular-nums ${scoreColor(val)}`}>
                  {val}/10
                </span>
              </div>
              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${barColor(val)}`}
                  style={{ width: `${val * 10}%` }}
                />
              </div>
              <p className="text-xs text-slate-600 mt-0.5">{dim.desc}</p>
            </div>
          );
        })}
      </div>

      {/* Improvements */}
      {score.improvements.length > 0 && (
        <div className="border-t border-white/5 pt-4">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
            Quick Wins
          </p>
          <ul className="space-y-2">
            {score.improvements.map((tip, i) => (
              <li key={i} className="flex gap-2 text-sm text-slate-400">
                <span className="text-orange-500 shrink-0">→</span>
                {tip}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
