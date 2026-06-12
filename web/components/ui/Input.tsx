"use client";

import { forwardRef, InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className = "", id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-sm font-semibold text-[#3d3530]">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`
            w-full bg-white border rounded-[12px] px-4 py-3
            text-[#0f0e0d] text-sm placeholder-[#a09890]
            transition-all duration-150
            ${error
              ? "border-red-300 focus:border-red-400 focus:ring-2 focus:ring-red-100"
              : "border-[#e7e5e2] focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
            }
            disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-[#fafaf9]
            outline-none
            ${className}
          `}
          {...props}
        />
        {hint && !error && <p className="text-xs text-[#a09890]">{hint}</p>}
        {error && <p className="text-xs text-red-600">{error}</p>}
      </div>
    );
  }
);

Input.displayName = "Input";
