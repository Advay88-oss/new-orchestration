import { NextResponse } from 'next/server';
import { runPython } from '@/lib/python';
import { companyAccess } from '@/lib/local-only';
import { clientTenant, isOwner } from '@/lib/viewer';

export const dynamic = 'force-dynamic';

/**
 * The Brand Brain view's data: profile, knowledge stats, visual memory,
 * What's new, competitor patterns and source health — or, with `?q=`, a
 * hybrid knowledge search. Read-only; it never writes to the brain.
 */
export async function GET(req: Request) {
  const sp = new URL(req.url).searchParams;
  const q = (sp.get('q') || '').trim().slice(0, 300);
  const asked = (sp.get('tenant') || '').toLowerCase();
  // The owner reads any company's brain; a client only their own.
  const access = companyAccess('the brand brain', /^[a-z0-9][a-z0-9_-]{1,40}$/.test(asked) ? asked : null,
                               { publicRead: !q });
  if (access instanceof NextResponse) return access;
  const tenant = access.tenant || '';
  const t = tenant ? [tenant] : [];
  const args = ['-m', 'pipeline.brand_brain.dashboard', ...(q ? ['search', q, ...t] : ['overview', ...t])];
  const r = await runPython(args, 60_000);
  if (!r.ok) {
    return NextResponse.json(
      { ok: false, error: r.error || r.stderr.split('\n').filter(Boolean).slice(-1)[0] || 'brain unavailable' },
      { status: 503 },
    );
  }
  try {
    const out = JSON.parse(r.stdout);
    // Other companies' names are not a client's business.
    const own = clientTenant();
    if (!isOwner()) out.tenants = [own || tenant].filter(Boolean);
    return NextResponse.json(out);
  } catch {
    return NextResponse.json({ ok: false, error: 'unreadable brain output' }, { status: 500 });
  }
}
