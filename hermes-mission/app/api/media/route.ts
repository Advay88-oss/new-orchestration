import { NextResponse } from 'next/server';
import { isDeployed, assetKey, getBytes } from '@/lib/gcs';
import fs from 'fs';
import path from 'path';
import { bareName, mediaType } from '@/lib/safepath';

const REPO_ROOT = process.env.REPO_ROOT || (fs.existsSync('/app') ? '/app' : path.resolve(process.cwd(), '..'));

export const dynamic = 'force-dynamic';

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const filename = searchParams.get('file') || searchParams.get('filename') || '';
    if (!filename) {
      return NextResponse.json({ error: 'file param required' }, { status: 400 });
    }

    // A bare image or video name only: no folders, no dotfiles, no JSON.
    const safeName = bareName(path.basename(filename));
    const type = safeName ? mediaType(safeName) : null;
    if (!safeName || !type) {
      return NextResponse.json({ error: 'not a media file' }, { status: 400 });
    }

    // Deployed, the render lives in the state bucket rather than on a disk
    // this container has. Without this every meme and visual 404s and the
    // views fall back to "Visual ready to synthesize" over assets that were
    // rendered hours ago.
    if (isDeployed()) {
      const key = assetKey(safeName);
      const obj = key ? await getBytes(key) : null;
      if (!obj) {
        return NextResponse.json(
          { error: `not in state bucket: ${safeName}` },
          { status: 404 },
        );
      }
      return new NextResponse(obj.body, {
        headers: {
          'Content-Type': obj.contentType,
          'Cache-Control': 'public, max-age=31536000, immutable',
        },
      });
    }

    const candidates = [
      path.join(REPO_ROOT, 'hermes-mission/public', safeName),
      path.join(REPO_ROOT, 'pipeline/state', safeName),
      path.join(REPO_ROOT, 'pipeline/state/panels', safeName),
    ];

    for (const c of candidates) {
      if (fs.existsSync(c) && fs.statSync(c).isFile()) {
        const buffer = fs.readFileSync(c);
        const contentType = type;
        return new NextResponse(buffer, {
          headers: {
            'Content-Type': contentType,
            'Cache-Control': 'private, max-age=3600',
            'X-Content-Type-Options': 'nosniff',
          },
        });
      }
    }

    return NextResponse.json({ error: `File not found: ${safeName}` }, { status: 404 });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
