"use client";

import { motion, Variants } from "framer-motion";
import React, { ReactNode } from "react";

// ── Shared easing presets ──────────────────────────────────────────────────
export const ease = {
  smooth:  [0.25, 0.1, 0.25, 1] as const,
  spring:  { type: "spring", stiffness: 280, damping: 26 },
  snappy:  { type: "spring", stiffness: 380, damping: 30 },
};

// ── Fade up ─────────────────────────────────────────────────────────────────
export const fadeUp: Variants = {
  hidden:  { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: ease.smooth } },
};

export const fadeIn: Variants = {
  hidden:  { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.4, ease: ease.smooth } },
};

// ── Stagger container ────────────────────────────────────────────────────────
export const stagger: Variants = {
  hidden:  {},
  visible: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
};

// ── Scale in (modal / card) ──────────────────────────────────────────────────
export const scaleIn: Variants = {
  hidden:  { opacity: 0, scale: 0.96, y: 8 },
  visible: { opacity: 1, scale: 1, y: 0, transition: { duration: 0.35, ease: ease.smooth } },
};

// ── Slide in from left ───────────────────────────────────────────────────────
export const slideRight: Variants = {
  hidden:  { opacity: 0, x: -16 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.4, ease: ease.smooth } },
};

// ── Page wrapper ─────────────────────────────────────────────────────────────
export function PageWrapper({ children }: { children: ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: ease.smooth }}
    >
      {children}
    </motion.div>
  );
}

// ── Reveal on scroll ─────────────────────────────────────────────────────────
export function Reveal({
  children,
  delay = 0,
  className = "",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-60px" }}
      variants={{
        hidden:  { opacity: 0, y: 24 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.55, ease: ease.smooth, delay } },
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// ── Stagger group ─────────────────────────────────────────────────────────────
export function StaggerGroup({
  children,
  className = "",
  style,
}: {
  children: ReactNode;
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-40px" }}
      variants={stagger}
      className={className}
      style={style}
    >
      {children}
    </motion.div>
  );
}

// ── Stagger item ──────────────────────────────────────────────────────────────
export function StaggerItem({
  children,
  className = "",
  style,
}: {
  children: ReactNode;
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <motion.div variants={fadeUp} className={className} style={style}>
      {children}
    </motion.div>
  );
}
