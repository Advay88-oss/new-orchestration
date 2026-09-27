/**
 * In-process rate limits for the dashboard's own routes (one instance on
 * Cloud Run, so memory is the whole picture). The pipeline's own limits —
 * assistant turns, cycles, the daily budget — live in pipeline/ops/budget.py
 * and hold across every process.
 */
const g = globalThis as unknown as { __vnLimits?: Map<string, number[]> };
const hits: Map<string, number[]> = (g.__vnLimits ??= new Map());

/** true when `key` may go ahead: at most `max` times per `windowMs`. */
export function allow(key: string, max: number, windowMs: number): boolean {
  const now = Date.now();
  const list = (hits.get(key) || []).filter((t) => now - t < windowMs);
  if (list.length >= max) { hits.set(key, list); return false; }
  list.push(now);
  hits.set(key, list);
  if (hits.size > 5000) for (const k of Array.from(hits.keys()).slice(0, 1000)) hits.delete(k);
  return true;
}

export function clientIp(req: Request): string {
  return (req.headers.get('x-forwarded-for') || '').split(',')[0].trim() || req.headers.get('x-real-ip') || 'local';
}
