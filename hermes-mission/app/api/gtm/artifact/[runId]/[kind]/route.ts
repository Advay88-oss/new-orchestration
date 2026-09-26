import { gtmArtifact } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

/**
 * Serve a run's rendered PNG or MP4.
 *
 * The assets live outside Next's public directory — under pipeline/state
 * locally, in GCS when deployed — so without this route the dashboard could
 * list an asset it could not display.
 */
export async function GET(
  _req: Request,
  { params }: { params: { runId: string; kind: string } },
) {
  const kind =
    params.kind === 'video' ? 'video' : params.kind === 'meme' ? 'meme' : 'visual';
  const got = await gtmArtifact(params.runId, kind);
  if (!got) return new Response('artifact not found', { status: 404 });

  return new Response(got.body, {
    headers: {
      'Content-Type': got.contentType,
      'Cache-Control': 'private, max-age=3600',  // per viewer: lib/viewer.ts
    },
  });
}
