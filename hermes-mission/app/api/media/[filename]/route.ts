import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { bareName, mediaType, within } from '@/lib/safepath';

const REPO_ROOT = process.env.REPO_ROOT || (fs.existsSync('/app') ? '/app' : path.resolve(process.cwd(), '..'));

// Panel images and videos only, by bare file name, from these folders.
const FOLDERS = ['hermes-mission/public', 'pipeline/state', 'pipeline/state/panels'];

export const dynamic = 'force-dynamic';

export async function GET(_req: Request, { params }: { params: { filename: string } }) {
  const name = bareName(params.filename);
  const type = name ? mediaType(name) : null;
  if (!name || !type) return NextResponse.json({ error: 'not a media file' }, { status: 400 });

  for (const folder of FOLDERS) {
    const file = within(path.join(REPO_ROOT, folder), name);
    if (!file) continue;
    try {
      if (!fs.statSync(file).isFile()) continue;
    } catch {
      continue;
    }
    return new NextResponse(fs.readFileSync(file), {
      headers: { 'Content-Type': type, 'Cache-Control': 'private, max-age=3600', 'X-Content-Type-Options': 'nosniff' },
    });
  }
  return NextResponse.json({ error: 'not found' }, { status: 404 });
}
