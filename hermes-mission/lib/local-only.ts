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
import { isOwner } from '@/lib/viewer';

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
