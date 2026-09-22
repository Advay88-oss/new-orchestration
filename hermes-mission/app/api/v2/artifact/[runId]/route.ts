import { NextResponse } from 'next/server';
import fs from 'fs';
import { artifactPath } from '@/lib/v2';

export const dynamic = 'force-dynamic';

const TYPES: Record<string, string> = {
  '.png': 'image/png', '.jpg': 'image/jpeg', '.json': 'application/json',
  '.html': 'text/html', '.mp4': 'video/mp4',
};

export async function GET(req: Request, { params }: { params: { runId: string } }) {
  const rel = new URL(req.url).searchParams.get('path');
  if (!rel || rel.includes('..')) {
    return NextResponse.json({ error: 'path required' }, { status: 400 });
  }
  const p = artifactPath(params.runId, rel);
  if (!fs.existsSync(p)) return NextResponse.json({ error: 'not found' }, { status: 404 });
  const ext = p.slice(p.lastIndexOf('.'));
  return new NextResponse(fs.readFileSync(p), {
    headers: { 'Content-Type': TYPES[ext] ?? 'application/octet-stream' },
  });
}
