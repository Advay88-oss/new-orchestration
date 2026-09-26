import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const REPO_ROOT = process.env.REPO_ROOT || (fs.existsSync('/app') ? '/app' : path.resolve(process.cwd(), '..'));

export const dynamic = 'force-dynamic';

export async function GET(req: Request, { params }: { params: { filename: string } }) {
  try {
    const filename = params.filename;
    
    // Search in public, pipeline/state, and root
    const candidates = [
      path.join(REPO_ROOT, 'hermes-mission/public', filename),
      path.join(REPO_ROOT, 'pipeline/state', filename),
      path.join(REPO_ROOT, 'pipeline/state/panels', filename),
      path.join(REPO_ROOT, filename),
    ];

    for (const c of candidates) {
      if (fs.existsSync(c) && fs.statSync(c).isFile()) {
        const buffer = fs.readFileSync(c);
        const ext = path.extname(filename).toLowerCase();
        let contentType = 'application/octet-stream';
        if (ext === '.png') contentType = 'image/png';
        else if (ext === '.jpg' || ext === '.jpeg') contentType = 'image/jpeg';
        else if (ext === '.webp') contentType = 'image/webp';
        else if (ext === '.svg') contentType = 'image/svg+xml';
        else if (ext === '.mp4') contentType = 'video/mp4';
        else if (ext === '.json') contentType = 'application/json';

        return new NextResponse(buffer, {
          headers: {
            'Content-Type': contentType,
            'Cache-Control': 'public, max-age=31536000, immutable',
          },
        });
      }
    }

    return NextResponse.json({ error: `File not found: ${filename}` }, { status: 404 });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
