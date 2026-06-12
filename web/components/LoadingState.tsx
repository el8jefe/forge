"use client";

import { useEffect, useState } from "react";

const STEPS = [
  { label: "Searching for business data…", pct: 15 },
  { label: "Analyzing your market…", pct: 35 },
  { label: "Writing your copy with Claude AI…", pct: 65 },
  { label: "Scoring your site quality…", pct: 85 },
  { label: "Almost done…", pct: 95 },
];

const STEP_DURATION = 1800;

export default function LoadingState() {
  const [stepIdx, setStepIdx] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setStepIdx((i) => Math.min(i + 1, STEPS.length - 1));
    }, STEP_DURATION);
    return () => clearInterval(timer);
  }, []);

  const current = STEPS[stepIdx];

  return (
    <div className="w-full max-w-xl mx-auto mt-8 animate-fade-in">
      <div className="bg-white/5 border border-white/10 rounded-2xl p-8">
        <div className="flex flex-col items-center text-center gap-6">
          {/* Animated icon */}
          <div className="relative">
            <div className="w-16 h-16 rounded-full border-2 border-orange-500/30 flex items-center justify-center">
              <div className="w-10 h-10 rounded-full border-2 border-t-orange-500 border-orange-500/20 animate-spin" />
            </div>
            <div className="absolute inset-0 flex items-center justify-center text-2xl">
              ✨
            </div>
          </div>

          <div>
            <p className="text-white font-medium text-lg">{current.label}</p>
            <p className="text-slate-500 text-sm mt-1">This takes about 10–15 seconds</p>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
            <div
              className="h-full bg-orange-500 rounded-full transition-all duration-1000 ease-out"
              style={{ width: `${current.pct}%` }}
            />
          </div>

          {/* Step indicators */}
          <div className="flex gap-1.5">
            {STEPS.map((_, i) => (
              <div
                key={i}
                className={`w-1.5 h-1.5 rounded-full transition-all ${
                  i <= stepIdx ? "bg-orange-500" : "bg-white/10"
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
