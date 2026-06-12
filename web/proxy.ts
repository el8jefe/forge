import { NextRequest, NextResponse } from "next/server";

// Auth guard disabled — Supabase stores session in localStorage (client-side only),
// so server-side cookie checks always fail and cause redirect loops.
// Route protection is handled client-side in each page instead.
export async function proxy(_req: NextRequest) {
  return NextResponse.next();
}

export const config = {
  matcher: ["/generate", "/dashboard", "/billing", "/auth/login", "/auth/signup"],
};
