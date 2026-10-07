import { NextResponse } from 'next/server';
import { companyAccess } from '@/lib/local-only';
import { lastJson, pythonPath, runPython, spawnHidden } from '@/lib/python';
import { REPO_ROOT } from '@/lib/v2';

export const dynamic = 'force-dynamic';

/**
 * The brands Vanna takes inspiration from (pipeline.brand_brain.inspiration).
 *
 * POST {tenant, action: "add", name, x_handle?, subreddit?}  add a brand and fetch its last 30 days
 * POST {tenant, action: "refresh", id}                       fetch again
 * POST {tenant, action: "remove", id}                        drop it from the section
 *
 * Add and refresh take a minute or two (X through Apify, Reddit, one model
 * call), so they run detached; the Brand Brain overview reports their state.
 */
const TENANT = /^[a-z0-9][a-z0-9_-]{1,40}$/;
const ID = /^[a-z0-9-]{1,40}$/;
const HANDLE = /^[A-Za-z0-9_]{1,30}$/;

/** A bare handle, @handle, or an x.com / twitter.com link. */
function xHandle(raw: string): string {
  let s = String(raw || '').trim();
  try {
    if (/^https?:\/\//i.test(s)) {
      const u = new URL(s);
      const host = u.hostname.replace(/^www\./, '').toLowerCase();
      if (host === 'x.com' || host === 'twitter.com' || host === 'mobile.twitter.com') {
        s = u.pathname.split('/').filter(Boolean)[0] || '';
      }
    }
  } catch { /* a non-URL falls through to the handle check */ }
  return s.replace(/^@/, '').split(/[/?#]/)[0];
}

/** One company's inspiration brands: their posts and the metrics on them. */
export async function GET(req: Request) {
  const asked = (new URL(req.url).searchParams.get('tenant') || '').toLowerCase();
  if (asked && !TENANT.test(asked)) return NextResponse.json({ ok: false, error: 'bad tenant' }, { status: 400 });
  const access = companyAccess('the brands this company learns from', asked || null);
  if (access instanceof NextResponse) return access;
  const tenant = access.tenant || asked;
  const r = await runPython(['-m', 'pipeline.brand_brain.mcp_call', 'inspiration', 'list', ...(tenant ? [tenant] : [])], 60_000);
  return NextResponse.json(lastJson(r.stdout) ?? { ok: false, error: r.stderr.slice(-300) || r.error || 'unavailable' });
}

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const asked = String(body.tenant || '').toLowerCase();
  const access = companyAccess('the brands Vanna learns from', asked || null, { write: true });
  if (access instanceof NextResponse) return access;
  const tenant = access.tenant || asked;
  if (!TENANT.test(tenant)) return NextResponse.json({ ok: false, error: 'bad tenant' }, { status: 400 });
  const action = String(body.action || '');

  let args: string[];
  if (action === 'add') {
    let name = String(body.name || '').trim().slice(0, 80);
    const fromName = xHandle(name);
    if (/^(https?:\/\/)?(www\.)?(x|twitter|mobile\.twitter)\.com\//i.test(name) && HANDLE.test(fromName)) {
      name = fromName;
    }
    if (!name) return NextResponse.json({ ok: false, error: 'a brand needs a name' }, { status: 400 });
    args = ['add', tenant, name.slice(0, 60)];
    const x = xHandle(String(body.x_handle || ''));
    const sub = String(body.subreddit || '').trim().replace(/^\/?r\//, '');
    if (x) {
      if (!HANDLE.test(x)) return NextResponse.json({ ok: false, error: 'bad X handle' }, { status: 400 });
      args.push('--x', x);
    }
    if (sub) {
      if (!/^[A-Za-z0-9_]{2,30}$/.test(sub)) return NextResponse.json({ ok: false, error: 'bad subreddit' }, { status: 400 });
      args.push('--subreddit', sub);
    }
  } else if (action === 'refresh' || action === 'remove') {
    const id = String(body.id || '');
    if (!ID.test(id)) return NextResponse.json({ ok: false, error: 'bad brand id' }, { status: 400 });
    args = [action, tenant, id];
  } else {
    return NextResponse.json({ ok: false, error: 'unknown action' }, { status: 400 });
  }

  if (action === 'remove') {
    const r = await runPython(['-m', 'pipeline.brand_brain.mcp_call', 'inspiration', ...args], 60_000);
    return NextResponse.json({ ok: r.ok, error: r.ok ? undefined : r.error || r.stderr.slice(-300) });
  }
  const py = pythonPath();
  if (!py) return NextResponse.json({ ok: false, error: 'no python interpreter for the pipeline' }, { status: 500 });
  const child = spawnHidden(['-m', 'pipeline.brand_brain.mcp_call', 'inspiration', ...args], {
    cwd: REPO_ROOT, detached: true, stdio: 'ignore',
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONPATH: REPO_ROOT },
  });
  child.unref();
  return NextResponse.json({ ok: true, state: 'running', action });
}
