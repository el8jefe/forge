import Link from "next/link";

// I-beam silhouette — structural steel, the backbone of trade work
export function TBIcon({ size = 20 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 20 20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Top flange */}
      <rect x="2" y="1.5" width="16" height="3.5" rx="1" fill="#f97316" />
      {/* Web (vertical member) */}
      <rect x="8.25" y="5" width="3.5" height="10" fill="#f97316" />
      {/* Bottom flange */}
      <rect x="2" y="15" width="16" height="3.5" rx="1" fill="#f97316" />
    </svg>
  );
}

interface TradeBuiltLogoProps {
  href?: string;
  size?: number;
  fontSize?: number;
}

export function TradeBuiltLogo({ href = "/", size = 20, fontSize = 17 }: TradeBuiltLogoProps) {
  const inner = (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <TBIcon size={size} />
      <span
        style={{
          fontWeight: 900,
          fontSize,
          letterSpacing: "-0.04em",
          color: "#f4f4f5",
        }}
      >
        TradeBuilt
      </span>
    </div>
  );

  if (!href) return inner;

  return (
    <Link href={href} style={{ textDecoration: "none" }}>
      {inner}
    </Link>
  );
}
