/**
 * Who is looking, and how far back they may see.
 *
 * The deployed dashboard is a public link. A visitor sees only the runs that
 * started after they first opened it, so a link sent today shows today's work
 * rather than every experiment before it. Nothing is deleted: every run stays
 * in the bucket, and the owner sees all of them.
 *
 *   owner    locally always; deployed, after opening the site once with
 *            `?key=<OWNER_KEY>` (middleware.ts sets an httpOnly cookie holding
 *            a hash of the key, never the key itself). `?key=` clears it.
 *            `?as=visitor` previews the visitor's view, `?as=owner` ends it.
 *   client   a company's own login: `?client=<link>` (made by the owner in
 *            Brand Brain) sets `vn_client`, a signed token naming ONE tenant.
 *            A client sees and runs everything for that company — its runs,
 *            Assistant, Brand Brain, Notion, launches, decisions — and
 *            nothing of any other company.
 *   visitor  everyone else. `vn_since` is set by the middleware on the first
 *            page load; a request without it sees no past runs at all.
 *
 * Run ids are `GTM-YYYYMMDD-HHMMSS` in UTC, so visibility is a string compare.
 */
import crypto from 'crypto';
import { cookies } from 'next/headers';
import { isDeployed } from '@/lib/gcs';

export const SINCE_COOKIE = 'vn_since';
export const OWNER_COOKIE = 'vn_owner';
export const PREVIEW_COOKIE = 'vn_preview';
export const CLIENT_COOKIE = 'vn_client';

const TENANT = /^[a-z0-9][a-z0-9_-]{1,40}$/;

function linkSecret(): string {
  return process.env.CLIENT_LINK_SECRET || process.env.BRAIN_INVITE_SECRET || process.env.OWNER_KEY
    || (isDeployed() ? '' : 'local-dev-client-links');
}

function b64u(buf: Buffer): string {
  return buf.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/** A client link token for one tenant: base64url(payload).base64url(hmac). */
export function signClient(tenant: string, days = 30): string {
  const secret = linkSecret();
  if (!secret || !TENANT.test(tenant)) throw new Error('cannot sign a client link');
  const body = b64u(Buffer.from(JSON.stringify({
    t: tenant, e: Math.floor(Date.now() / 1000) + days * 86400, n: crypto.randomBytes(6).toString('hex'),
  })));
  const sig = b64u(crypto.createHmac('sha256', secret).update('vn-client:' + body).digest());
  return body + '.' + sig;
}

/** The tenant a client token names, or null if it is missing, forged or expired. */
export function verifyClient(token: string | undefined | null): { tenant: string; exp: number } | null {
  const secret = linkSecret();
  if (!token || !secret) return null;
  const [body, sig] = String(token).split('.');
  if (!body || !sig) return null;
  const want = b64u(crypto.createHmac('sha256', secret).update('vn-client:' + body).digest());
  if (want.length !== sig.length || !crypto.timingSafeEqual(Buffer.from(want), Buffer.from(sig))) return null;
  try {
    const p = JSON.parse(Buffer.from(body.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf-8'));
    if (!TENANT.test(String(p.t)) || !(Number(p.e) > Date.now() / 1000)) return null;
    return { tenant: String(p.t), exp: Number(p.e) };
  } catch {
    return null;
  }
}

/** The company this browser is a client of (never for the owner or a preview). */
export function clientTenant(): string | null {
  if (jar()?.get(PREVIEW_COOKIE)?.value === 'visitor') return null;
  if (isOwner()) return null;
  return verifyClient(jar()?.get(CLIENT_COOKIE)?.value)?.tenant ?? null;
}

export type Role = 'owner' | 'client' | 'visitor';

export function role(): Role {
  if (isOwner()) return 'owner';
  return clientTenant() ? 'client' : 'visitor';
}

const RUN_ID = /^GTM-(\d{8}-\d{6})$/;

/** The owner cookie's value for a key. middleware.ts computes the same hash. */
export function ownerHash(key: string): string {
  return crypto.createHash('sha256').update('vn-owner:' + key).digest('hex');
}

function jar() {
  try {
    return cookies();
  } catch {
    return null;                          // outside a request (build, scripts)
  }
}

export function isOwner(): boolean {
  if (jar()?.get(PREVIEW_COOKIE)?.value === 'visitor') return false;
  // Locally the owner is the default viewer, unless this browser opened a
  // client link (so the client view can be tried on the laptop).
  if (!isDeployed()) return !verifyClient(jar()?.get(CLIENT_COOKIE)?.value);
  const key = process.env.OWNER_KEY;
  if (!key) return false;
  const got = jar()?.get(OWNER_COOKIE)?.value ?? '';
  const want = ownerHash(key);
  return got.length === want.length && crypto.timingSafeEqual(Buffer.from(got), Buffer.from(want));
}

/** When this visitor first opened the dashboard, or null for the owner and
 * for a client (who sees every run of their own company, filtered by tenant
 * in lib/gtm.ts rather than by date). */
export function viewerSince(): Date | null {
  if (isOwner() || clientTenant()) return null;
  const raw = jar()?.get(SINCE_COOKIE)?.value;
  const d = raw ? new Date(raw) : new Date();
  return Number.isNaN(d.getTime()) ? new Date() : d;
}

function stamp(d: Date): string {
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getUTCFullYear()}${p(d.getUTCMonth() + 1)}${p(d.getUTCDate())}-` +
    `${p(d.getUTCHours())}${p(d.getUTCMinutes())}${p(d.getUTCSeconds())}`;
}

/** A filter for run ids this viewer may see. */
export function runVisibility(): (runId: string) => boolean {
  const since = viewerSince();
  if (!since) return () => true;
  const cut = stamp(since);
  return (runId) => {
    const m = RUN_ID.exec(runId);
    return Boolean(m) && m![1] >= cut;
  };
}

export function canSeeRun(runId: string): boolean {
  return runVisibility()(runId);
}

/**
 * An Ideas or Memes panel as this viewer may see it: only items made by runs
 * they may see (an item with no run is older than any visitor), with the
 * panel's counts recomputed from what is left. The owner gets it unchanged.
 */
export function scopePanel(data: any, kind: 'ideas' | 'memes'): any {
  if (!viewerSince() || !data || !Array.isArray(data[kind])) return data;
  const see = runVisibility();
  const items = data[kind].filter((it: any) => typeof it?.run_id === 'string' && see(it.run_id));
  const out = { ...data, [kind]: items };
  if (kind === 'ideas') {
    out.total_ideas = items.length;
    out.runnable_today_count = items.filter((i: any) => i.runnable_today).length;
    out.blocked_count = items.length - out.runnable_today_count;
  } else {
    out.total_memes = items.length;
    for (const r of ['low', 'medium', 'high']) {
      out[`${r}_risk_count`] = items.filter((m: any) => String(m.risk || '').toLowerCase() === r).length;
    }
  }
  return out;
}

/**
 * The learning overview as this viewer may see it. The bandit's records are
 * the sum of every past run, so for a visitor they are rebuilt from the reward
 * events of the runs they may see: a fresh link starts at zero.
 */
export function scopeLearning(data: any): any {
  if (!viewerSince() || !data || !Array.isArray(data.events)) return data;
  const see = runVisibility();
  const events = data.events.filter((e: any) => typeof e?.run_id === 'string' && see(e.run_id));
  const pairs = (Array.isArray(data.pairs) ? data.pairs : [])
    .filter((p: any) => typeof p?.run_id === 'string' && see(p.run_id));
  const arms: Record<string, { option: string; alpha: number; beta: number; n: number; mean: number }[]> = {};
  for (const dim of Object.keys(data.arms || {})) {
    const by = new Map<string, { a: number; b: number; n: number }>();
    for (const e of events) {
      const opt = e.arms?.[dim];
      if (typeof opt !== 'string') continue;
      const r = Math.min(1, Math.max(0, Number(e.total) || 0));
      const s = by.get(opt) || { a: 1, b: 1, n: 0 };
      s.a += r; s.b += 1 - r; s.n += 1;
      by.set(opt, s);
    }
    arms[dim] = [...by].map(([option, s]) => ({
      option, alpha: +s.a.toFixed(3), beta: +s.b.toFixed(3), n: s.n, mean: +(s.a / (s.a + s.b)).toFixed(3),
    })).sort((x, y) => y.mean - x.mean);
  }
  return { ...data, arms, events, n_events: events.length, pairs, n_pairs: pairs.length };
}

export function viewer() {
  const since = viewerSince();
  const previewing = jar()?.get(PREVIEW_COOKIE)?.value === 'visitor';
  const r = role();
  return { owner: r === 'owner', role: r, client: r === 'client' ? clientTenant() : null,
           previewing, since: since ? since.toISOString() : null };
}
