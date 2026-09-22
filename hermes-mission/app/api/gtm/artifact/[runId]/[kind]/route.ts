import fs from 'fs';
import { gtmArtifactPath } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

/**
 * Serve a run's rendered PNG or MP4.
 *
 * The visuals live under `pipeline/state`, outside Next's public directory, so
 * without this route the dashboard could list an asset it could not display —
 * which is how "visuals are generated but not rendered here" happened.
 */
export async function GET(
  _req: Request,
  { params }: { params: { runId: string; kind: string } },
) {
  const kind =
    params.kind === 'video' ? 'video' : params.kind === 'meme' ? 'meme' : 'visual';
  const file = gtmArtifactPath(params.runId, kind);
  if (!file) return new Response('artifact not found', { status: 404 });

  const body = fs.readFileSync(file);
  return new Response(body, {
    headers: {
      'Content-Type': kind === 'video' ? 'video/mp4' : 'image/png',
      'Cache-Control': 'public, max-age=3600',
    },
  });
}
