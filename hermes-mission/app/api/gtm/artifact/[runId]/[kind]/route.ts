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
  req: Request,
  { params }: { params: { runId: string; kind: string } },
) {
  const kind =
    params.kind === 'video' ? 'video' : params.kind === 'meme' ? 'meme' : 'visual';
  const got = await gtmArtifact(params.runId, kind);
  if (!got) return new Response('artifact not found', { status: 404 });

  const headers: Record<string, string> = {
    'Content-Type': got.contentType,
    'Cache-Control': 'private, max-age=3600',  // per viewer: lib/viewer.ts
    'Accept-Ranges': 'bytes',
  };
  // A video player asks for byte ranges to seek (Safari will not play
  // without them), so answer a Range with 206 and that slice.
  const size = got.body.length;
  const m = /^bytes=(\d*)-(\d*)$/.exec(req.headers.get('range') || '');
  if (m && (m[1] || m[2])) {
    let start = m[1] ? Number(m[1]) : Math.max(0, size - Number(m[2]));
    let end = m[1] && m[2] ? Number(m[2]) : size - 1;
    end = Math.min(end, size - 1);
    if (start > end || start >= size) {
      return new Response(null, { status: 416, headers: { ...headers, 'Content-Range': `bytes */${size}` } });
    }
    start = Math.max(0, start);
    return new Response(got.body.subarray(start, end + 1), {
      status: 206,
      headers: { ...headers, 'Content-Range': `bytes ${start}-${end}/${size}`, 'Content-Length': String(end - start + 1) },
    });
  }
  return new Response(got.body, { headers: { ...headers, 'Content-Length': String(size) } });
}
