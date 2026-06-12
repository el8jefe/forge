"use client";

import { motion, HTMLMotionProps } from "framer-motion";

interface CardProps extends HTMLMotionProps<"div"> {
  hover?: boolean;
  padding?: "sm" | "md" | "lg" | "none";
}

const paddingMap = { none: "", sm: "p-4", md: "p-5", lg: "p-6 md:p-8" };

export function Card({ hover = false, padding = "md", className = "", children, ...props }: CardProps) {
  return (
    <motion.div
      whileHover={hover ? { y: -3, boxShadow: "0 16px 48px rgba(0,0,0,0.10)" } : undefined}
      transition={{ type: "spring", stiffness: 300, damping: 24 }}
      className={`
        bg-white border border-[#e7e5e2] rounded-[16px]
        shadow-[0_1px_4px_rgba(0,0,0,0.06)]
        ${paddingMap[padding]}
        ${className}
      `}
      {...props}
    >
      {children}
    </motion.div>
  );
}
