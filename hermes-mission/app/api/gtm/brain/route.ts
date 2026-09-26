import { NextResponse } from 'next/server';
import { runPython } from '@/lib/python';

export const dynamic = 'force-dynamic';

/**
 * The Brand Brain view's data: profile, knowledge stats, visual memory,
 * What's new, competitor patterns and source health — or, with `?q=`, a
 * hybrid knowledge search. Read-only; it never writes to the brain.
 */
export async function GET(req: Request) {
  const sp = new URL(req.url).searchParams;
  const q = (sp.get('q') || '').trim().slice(0, 300);
  const tenant = (sp.get('tenant') || '').toLowerCase();
  const t = /^[a-z0-9][a-z0-9_-]{1,40}$/.test(tenant) ? [tenant] : [];
  const args = ['-m', 'pipeline.brand_brain.dashboard', ...(q ? ['search', q, ...t] : ['overview', ...t])];
  const r = await runPython(args, 60_000);
  if (!r.ok) {
    return NextResponse.json(
      { ok: false, error: r.error || r.stderr.split('\n').filter(Boolean).slice(-1)[0] || 'brain unavailable' },
      { status: 503 },
    );
  }
  try {
    return NextResponse.json(JSON.parse(r.stdout));
  } catch {
    return NextResponse.json({ ok: false, error: 'unreadable brain output' }, { status: 500 });
  }
}
