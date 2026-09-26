import fs from 'fs';
import os from 'os';
import path from 'path';
import { NextResponse } from 'next/server';
import { localOnly } from '@/lib/local-only';
import { runPython } from '@/lib/python';

export const dynamic = 'force-dynamic';

/**
 * The brand profile under review.
 *
 * GET  ?version=N   one version in full (the newest when omitted)
 * POST {action: "approve", version}          the founder approves a version
 * POST {action: "save", profile, note}       an edit, saved as a new DRAFT
 *
 * Writes are local-only: the deployed dashboard is public and must never be
 * able to change what the agents say about the brand.
 */
async function py(args: string[]) {
  const r = await runPython(['-m', 'pipeline.brand_brain.dashboard', ...args], 120_000);
  if (!r.ok) {
    return NextResponse.json({ ok: false, error: r.error || r.stderr.split('\n').filter(Boolean).slice(-1)[0] }, { status: 500 });
  }
  try {
    return NextResponse.json(JSON.parse(r.stdout));
  } catch {
    return NextResponse.json({ ok: false, error: 'unreadable brain output' }, { status: 500 });
  }
}

export async function GET(req: Request) {
  const v = new URL(req.url).searchParams.get('version') || '';
  return py(['profile', ...(/^\d+$/.test(v) ? [v] : [])]);
}

export async function POST(req: Request) {
  const blocked = localOnly('changing the brand profile');
  if (blocked) return blocked;
  const body = await req.json().catch(() => ({}));
  if (body.action === 'approve' && Number.isInteger(body.version)) {
    return py(['approve', String(body.version)]);
  }
  if (body.action === 'save' && body.profile && typeof body.profile === 'object') {
    const file = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'brain-')), 'profile.json');
    fs.writeFileSync(file, JSON.stringify(body.profile), 'utf-8');
    try {
      return await py(['save', file, String(body.note || '').slice(0, 300)]);
    } finally {
      fs.rmSync(path.dirname(file), { recursive: true, force: true });
    }
  }
  return NextResponse.json({ ok: false, error: 'action approve {version} or save {profile, note}' }, { status: 400 });
}
