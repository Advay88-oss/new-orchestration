/**
 * Who is looking, and what they see.
 *
 * One link, no owner/visitor split (2026-10-08): whoever opens the dashboard
 * can do everything — chat, launch, schedule, add a company. What differs is
 * only what each BROWSER sees:
 *
 *   fresh    by default a browser sees the runs started after it first opened
 *            the link (`vn_since`, set by the middleware, signed) and the
 *            chats it started itself. A new person starts with a clean slate.
 *   all      `?all` on any page shows this browser the whole history, every
 *            run and every chat; `?fresh` starts it over. On the laptop
 *            (not deployed) everything is always shown.
 *   client   a company's client link (`?client=<signed link>`) still sees
 *            and acts for that one company only.
 *
 * Run ids are `GTM-YYYYMMDD-HHMMSS` in UTC, so visibility is a string compare.
 */
import crypto from 'crypto';
import { cookies } from 'next/headers';
import { isDeployed } from '@/lib/gcs';

export const SINCE_COOKIE = 'vn_since';
export const OWNER_COOKIE = 'vn_owner';
export const PREVIEW_COOKIE = 'vn_preview';
export const ALL_COOKIE = 'vn_all';
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
  return verifyClient(jar()?.get(CLIENT_COOKIE)?.value)?.tenant ?? null;
}

/** This browser asked to see the whole history (`?all`), or this is the laptop. */
export function seesAll(): boolean {
  if (clientTenant()) return false;
  return !isDeployed() || jar()?.get(ALL_COOKIE)?.value === '1';
}

/** The one company this viewer may see runs of: a client's own; everyone
 * else sees every company (filtered by date for a fresh browser). */
export function scopeTenant(): string | null {
  return clientTenant();
}

export type Role = 'owner' | 'client' | 'visitor';

/** Who owns the chats this browser starts: "owner", "client:<tenant>", or
 * "visitor:<id>" — the id is a hash of the signed first-visit cookie, so it
 * is stable for the browser and says nothing about the person. */
export function viewerKey(): string {
  if (seesAll()) return 'owner';
  const own = clientTenant();
  if (own) return 'client:' + own;
  const since = jar()?.get(SINCE_COOKIE)?.value || '';
  return 'visitor:' + (since ? crypto.createHash('sha256').update('vn-viewer:' + since).digest('hex').slice(0, 16)
                             : 'anonymous');
}

/** What this viewer may DO: everything, except a client link (one company). */
export function role(): Role {
  return clientTenant() ? 'client' : 'owner';
}

const RUN_ID = /^GTM-(\d{8}-\d{6})$/;

function sessionSecret(): string {
  return process.env.SESSION_SECRET || process.env.OWNER_KEY || (isDeployed() ? '' : 'local-dev-session');
}

function hmacHex(secret: string, msg: string): string {
  return crypto.createHmac('sha256', secret).update(msg).digest('hex');
}

function sameText(a: string, b: string): boolean {
  const x = Buffer.from(a), y = Buffer.from(b);
  return x.length === y.length && crypto.timingSafeEqual(x, y);
}

/** The time a signed `vn_since` names, or null when it is missing or forged.
 * middleware.ts signs it with the same secret. */
function verifySince(raw: string | undefined): Date | null {
  const secret = sessionSecret();
  const m = /^(\d{9,11})\.([0-9a-f]{64})$/.exec(String(raw || ''));
  if (!secret || !m || !sameText(m[2], hmacHex(secret, 'vn-since:' + m[1]))) return null;
  return new Date(Number(m[1]) * 1000);
}

function jar() {
  try {
    return cookies();
  } catch {
    return null;                          // outside a request (build, scripts)
  }
}

/** May act on everything (every company, the schedule, onboarding). True
 * for anyone on the link; a client link acts for its own company only. */
export function isOwner(): boolean {
  return !clientTenant();
}

/** When this visitor first opened the dashboard, or null for the owner and
 * for a client (who sees every run of their own company, filtered by tenant
 * in lib/gtm.ts rather than by date). */
export function viewerSince(): Date | null {
  if (seesAll() || clientTenant()) return null;
  // Unsigned, forged or missing: from now on, so nothing older shows.
  return verifySince(jar()?.get(SINCE_COOKIE)?.value) ?? new Date();
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

/** True when this viewer may see something stamped `iso`. A visitor sees
 * only what happened after they first opened the link; an item with no
 * date is older than any visitor. */
export function seesSince(iso: unknown): boolean {
  const since = viewerSince();
  if (!since) return true;
  const t = Date.parse(String(iso || ''));
  return Number.isFinite(t) && t >= since.getTime();
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
  const r = role();
  return { owner: r === 'owner', role: r, client: r === 'client' ? clientTenant() : null,
           previewing: false, all: seesAll(), since: since ? since.toISOString() : null };
}
