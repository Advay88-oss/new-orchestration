import { NextResponse } from 'next/server';
import { localOnly } from '@/lib/local-only';
import { runPython } from '@/lib/python';

export const dynamic = 'force-dynamic';

/**
 * The learning loop's state: the contextual bandit's arms, founder locks,
 * reward events and preference pairs.
 *
 * GET                                             the overview
 * POST {action: "lock", dim, option}              lock an arm (the founder's override)
 * POST {action: "unlock", dim}
 * POST {action: "outcome", runId, metrics}        a published post's metrics
 *
 * Writes are local-only; the deployed dashboard is public.
 */
const DIMS = new Set(['pillar', 'hook_type', 'length']);

async function py(args: string[]) {
  const r = await runPython(args, 60_000);
  if (!r.ok) {
    return NextResponse.json({ ok: false, error: r.error || r.stderr.split('\n').filter(Boolean).slice(-1)[0] }, { status: 500 });
  }
  try {
    return NextResponse.json(JSON.parse(r.stdout.trim().split('\n').filter(Boolean).pop() || '{}'));
  } catch {
    return NextResponse.json({ ok: false, error: 'unreadable output' }, { status: 500 });
  }
}

export async function GET() {
  return py(['-m', 'pipeline.gtm_learning.bandit']);
}

export async function POST(req: Request) {
  const blocked = localOnly('changing the learning loop');
  if (blocked) return blocked;
  const b = await req.json().catch(() => ({}));
  if (b.action === 'lock' && DIMS.has(b.dim) && typeof b.option === 'string' && b.option.trim()) {
    return py(['-m', 'pipeline.gtm_learning.bandit', 'lock', b.dim, b.option.slice(0, 200)]);
  }
  if (b.action === 'unlock' && DIMS.has(b.dim)) {
    return py(['-m', 'pipeline.gtm_learning.bandit', 'unlock', b.dim]);
  }
  if (b.action === 'outcome' && /^GTM-\d{8}-\d{6}$/.test(String(b.runId)) && b.metrics && typeof b.metrics === 'object') {
    const m: Record<string, number> = {};
    for (const k of ['impressions', 'likes', 'reposts', 'replies', 'quotes', 'bookmarks', 'clicks', 'signups']) {
      const v = Number(b.metrics[k]);
      if (Number.isFinite(v) && v >= 0) m[k] = v;
    }
    return py(['-m', 'pipeline.gtm_learning.rewards', 'outcome', String(b.runId), JSON.stringify(m)]);
  }
  return NextResponse.json({ ok: false, error: 'lock {dim, option} | unlock {dim} | outcome {runId, metrics}' }, { status: 400 });
}
