import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { isDeployed, getText } from '@/lib/gcs';
import { seesSince } from '@/lib/viewer';

export const dynamic = 'force-dynamic';

/** Headlines and posts that just landed, so the dashboard can raise a notice. */
export async function GET() {
  let raw: string | null = null;
  if (isDeployed()) {
    raw = await getText('state/pipeline/state/notices.json');
  } else {
    try {
      raw = fs.readFileSync(path.join(process.cwd(), '..', 'pipeline', 'state', 'notices.json'), 'utf-8');
    } catch {
      raw = null;
    }
  }
  let notices: unknown[] = [];
  if (raw) {
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) notices = parsed.filter((n: any) => seesSince(n?.at)).slice(0, 20);
    } catch { /* an empty list is the same as no file */ }
  }
  return NextResponse.json({ success: true, notices });
}
