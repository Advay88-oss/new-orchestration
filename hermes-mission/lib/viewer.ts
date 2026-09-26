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
  if (!isDeployed()) return true;
  const key = process.env.OWNER_KEY;
  if (!key) return false;
  const got = jar()?.get(OWNER_COOKIE)?.value ?? '';
  const want = ownerHash(key);
  return got.length === want.length && crypto.timingSafeEqual(Buffer.from(got), Buffer.from(want));
}

/** When this visitor first opened the dashboard, or null for the owner. */
export function viewerSince(): Date | null {
  if (isOwner()) return null;
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

export function viewer() {
  const since = viewerSince();
  const previewing = jar()?.get(PREVIEW_COOKIE)?.value === 'visitor';
  return { owner: since === null, previewing, since: since ? since.toISOString() : null };
}
