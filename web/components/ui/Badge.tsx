type Variant = "orange" | "purple" | "green" | "gray" | "red" | "amber";

interface BadgeProps {
  variant?: Variant;
  children: React.ReactNode;
  size?: "sm" | "md";
  dot?: boolean;
  className?: string;
}

const styles: Record<Variant, string> = {
  orange: "bg-orange-50 text-orange-700 border-orange-100",
  purple: "bg-violet-50 text-violet-700 border-violet-100",
  green:  "bg-green-50 text-green-700 border-green-100",
  gray:   "bg-stone-50 text-stone-600 border-stone-200",
  red:    "bg-red-50 text-red-700 border-red-100",
  amber:  "bg-amber-50 text-amber-700 border-amber-100",
};

const dotStyles: Record<Variant, string> = {
  orange: "bg-orange-500",
  purple: "bg-violet-500",
  green:  "bg-green-500",
  gray:   "bg-stone-400",
  red:    "bg-red-500",
  amber:  "bg-amber-500",
};

const sizeStyles = {
  sm: "text-xs px-2 py-0.5",
  md: "text-xs px-2.5 py-1",
};

export function Badge({ variant = "gray", size = "md", dot = false, className = "", children }: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center gap-1.5 font-semibold rounded-full border
        ${styles[variant]}
        ${sizeStyles[size]}
        ${className}
      `}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotStyles[variant]}`} />}
      {children}
    </span>
  );
}
