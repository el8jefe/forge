"use client";

import { motion, HTMLMotionProps } from "framer-motion";
import { forwardRef } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends Omit<HTMLMotionProps<"button">, "ref"> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  fullWidth?: boolean;
}

const variantStyles: Record<Variant, string> = {
  primary:
    "bg-orange-500 text-white shadow-[0_4px_20px_rgba(249,115,22,0.3)] hover:bg-orange-600",
  secondary:
    "bg-white text-gray-900 border border-[#e7e5e2] shadow-[0_1px_4px_rgba(0,0,0,0.07)] hover:bg-[#fafaf9]",
  ghost:
    "bg-transparent text-gray-600 hover:bg-[#f5f4f2] hover:text-gray-900",
  danger:
    "bg-red-500 text-white shadow-[0_4px_16px_rgba(239,68,68,0.25)] hover:bg-red-600",
};

const sizeStyles: Record<Size, string> = {
  sm: "px-3.5 py-2 text-sm font-semibold rounded-[10px]",
  md: "px-5 py-2.5 text-sm font-semibold rounded-[12px]",
  lg: "px-7 py-3.5 text-base font-semibold rounded-[14px]",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", loading, fullWidth, className = "", children, disabled, ...props }, ref) => {
    return (
      <motion.button
        ref={ref}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.97 }}
        transition={{ type: "spring", stiffness: 400, damping: 25 }}
        disabled={disabled || loading}
        className={`
          inline-flex items-center justify-center gap-2
          transition-colors duration-150 select-none
          disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none
          ${variantStyles[variant]}
          ${sizeStyles[size]}
          ${fullWidth ? "w-full" : ""}
          ${className}
        `}
        {...props}
      >
        {loading ? (
          <>
            <svg className="animate-spin h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span>Loading…</span>
          </>
        ) : children}
      </motion.button>
    );
  }
);

Button.displayName = "Button";
