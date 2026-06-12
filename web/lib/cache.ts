import type { GenerateSiteResponse } from "./types";

// In-memory cache — resets on serverless cold start.
// Upgrade to Vercel KV or Redis for persistence at scale.
const cache = new Map<string, { data: GenerateSiteResponse; ts: number }>();
const TTL_MS = 1000 * 60 * 60 * 24; // 24 hours

export function getCacheKey(name: string, location: string): string {
  return `${name.toLowerCase().trim()}::${location.toLowerCase().trim()}`;
}

export function getCached(key: string): GenerateSiteResponse | null {
  const entry = cache.get(key);
  if (!entry) return null;
  if (Date.now() - entry.ts > TTL_MS) {
    cache.delete(key);
    return null;
  }
  return entry.data;
}

export function setCached(key: string, data: GenerateSiteResponse): void {
  cache.set(key, { data, ts: Date.now() });
  // Evict old entries if cache grows too large
  if (cache.size > 500) {
    const oldest = [...cache.entries()].sort((a, b) => a[1].ts - b[1].ts)[0];
    cache.delete(oldest[0]);
  }
}
