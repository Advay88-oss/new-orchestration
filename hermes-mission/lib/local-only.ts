/**
 * The guard for routes that drive the pipeline rather than read it.
 *
 * Three places this dashboard runs:
 *
 *   local            the founder's machine: everything is allowed.
 *   deployed, hybrid the Cloud Run dashboard with the pipeline on a laptop:
 *                    it can only read the bucket, so writes are refused with
 *                    a 501 saying where they run.
 *   deployed, cloud  VANNA_CLOUD=1: the pipeline, the brain (Cloud SQL) and
 *                    the jobs are on GCP too, so writes work — for the OWNER
 *                    only (the ?key=<OWNER_KEY> cookie, lib/viewer.ts). A
 *                    visitor to the public link gets a 403 and can change
 *                    nothing.
 *
 * `what` names the action in the operator's terms — "starting a run",
 * "the scheduler" — because this string is what the dashboard shows.
 */
import { NextResponse } from 'next/server';
import { isDeployed } from '@/lib/gcs';
import { clientTenant, isOwner } from '@/lib/viewer';

export function cloudMode(): boolean {
  return isDeployed() && process.env.VANNA_CLOUD === '1';
}

/**
 * The guard for data that belongs to the owner, not the public link: the brand
 * brain (profile, knowledge, images, competitors). Reads too, everywhere —
 * locally the owner is always the viewer unless previewing `?as=visitor`.
 */
export function ownerOnly(what: string): NextResponse | null {
  if (isOwner()) return null;
  return NextResponse.json(
    { success: false, ok: false, owner_only: true, error: `${what} is for the owner of this dashboard.` },
    { status: 403 },
  );
}

/**
 * Owner, or a client acting on their own company. Returns the tenant the
 * route must use — for a client always their own, whatever was asked for —
 * or the response to send (403 for a visitor or for another company; 501 on
 * the hybrid deployment where the pipeline is not in the cloud).
 */
export function companyAccess(what: string, requested?: string | null,
                              opts: { write?: boolean; publicRead?: boolean; publicChat?: boolean } = {}): { tenant: string | null } | NextResponse {
  if (opts.write && isDeployed() && !cloudMode()) return localOnly(what) as NextResponse;
  if (isOwner()) return { tenant: requested || null };
  const own = clientTenant();
  if (own) {
    if (requested && requested !== own) {
      return NextResponse.json({ success: false, ok: false, error: `${what}: this link is for ${own} only.` },
                               { status: 403 });
    }
    return { tenant: own };
  }
  // The public link can read this company's chats, name and research, and
  // can talk to the assistant (scrape, sources, a post). It cannot open
  // another company. The schedule drawer stays with the owner.
  if ((opts.publicRead && !opts.write) || opts.publicChat) {
    const tenant = String(process.env.BRAIN_TENANT || 'vanna').toLowerCase();
    if (requested && requested !== tenant) {
      return NextResponse.json({ success: false, ok: false, error: `${what}: this link is for ${tenant} only.` },
                               { status: 403 });
    }
    return { tenant };
  }
  return NextResponse.json(
    { success: false, ok: false, owner_only: true, error: `${what} is for the owner of this dashboard.` },
    { status: 403 },
  );
}

export function localOnly(what: string): NextResponse | null {
  if (!isDeployed()) return null;
  if (cloudMode()) {
    if (isOwner()) return null;
    return NextResponse.json(
      { success: false, ok: false, error: `${what} is for the owner of this dashboard.` },
      { status: 403 },
    );
  }
  return NextResponse.json(
    {
      success: false,
      deployed: true,
      error:
        `${what} needs the pipeline, which runs on the founder's machine. ` +
        'This dashboard is the read-only half of the GCS seam.',
    },
    { status: 501 },
  );
}
