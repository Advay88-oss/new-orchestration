/**
 * The guard for routes that drive the pipeline rather than read it.
 *
 * The 13 agents run on the founder's machine — they need the Chrome bridge,
 * the Brain DB, the font files and four minutes per cycle. The deployed
 * dashboard reads their output from GCS and can do nothing else.
 *
 * Without this, a route that spawns Python in the container fails with ENOENT
 * on a binary that was never installed, and the UI reports a broken pipeline
 * instead of a remote one. Worse for the write paths: a dismissal appended to
 * a container filesystem returns success and is gone at the next request.
 */
import { NextResponse } from 'next/server';
import { isDeployed } from '@/lib/gcs';

/**
 * A 501 explaining why, or null when running locally and free to proceed.
 *
 * `what` names the action in the operator's terms — "starting a run",
 * "the scheduler" — because this string is what the dashboard shows.
 */
export function localOnly(what: string): NextResponse | null {
  if (!isDeployed()) return null;
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
