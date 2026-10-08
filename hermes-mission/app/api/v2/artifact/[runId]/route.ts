import { NextResponse } from 'next/server';
import fs from 'fs';
import { artifactPath } from '@/lib/v2';
import { ownerOnly } from '@/lib/local-only';
import { RUN_ID, mediaType } from '@/lib/safepath';

export const dynamic = 'force-dynamic';

export async function GET(req: Request, { params }: { params: { runId: string } }) {
  const denied = ownerOnly('the v2 run files');
  if (denied) return denied;
  const rel = new URL(req.url).searchParams.get('path') || '';
  const type = mediaType(rel);
  if (!RUN_ID.test(params.runId) || !rel || !type) {
    return NextResponse.json({ error: 'a run id and an image or video path are required' }, { status: 400 });
  }
  const p = artifactPath(params.runId, rel);
  if (!p || !fs.existsSync(p)) return NextResponse.json({ error: 'not found' }, { status: 404 });
  return new NextResponse(fs.readFileSync(p), { headers: { 'Content-Type': type, 'X-Content-Type-Options': 'nosniff' } });
}
