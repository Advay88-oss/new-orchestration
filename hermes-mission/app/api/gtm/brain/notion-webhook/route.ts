import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { NextResponse } from 'next/server';
import { isDeployed } from '@/lib/gcs';
import { runPython } from '@/lib/python';
import { REPO_ROOT } from '@/lib/v2';

export const dynamic = 'force-dynamic';

/**
 * Notion webhooks — near-real-time freshness for the brand brain.
 *
 * Subscribing: Notion first POSTs {verification_token}. It is written to
 * pipeline/state/notion_verification_token.txt (never echoed back) for the
 * founder to paste into Notion, and to set as NOTION_WEBHOOK_SECRET.
 * Events: the body is signed — X-Notion-Signature: sha256=HMAC(secret, body).
 * A valid event marks the tenant (?tenant=, default vanna) for a Notion sync
 * at the next run start. Anything unsigned or mis-signed is refused.
 *
 * Deployed, this dashboard cannot reach the pipeline's brain; the event is
 * acknowledged and the daily freshness check picks the change up.
 */
const TENANT = /^[a-z0-9][a-z0-9_-]{1,40}$/;

export async function POST(req: Request) {
  const raw = await req.text();
  let body: any = {};
  try { body = JSON.parse(raw); } catch { /* not JSON */ }

  if (body && typeof body.verification_token === 'string') {
    if (!isDeployed()) {
      const f = path.join(REPO_ROOT, 'pipeline', 'state', 'notion_verification_token.txt');
      fs.mkdirSync(path.dirname(f), { recursive: true });
      fs.writeFileSync(f, body.verification_token, 'utf-8');
    }
    return NextResponse.json({ ok: true });
  }

  const secret = process.env.NOTION_WEBHOOK_SECRET || '';
  const sig = req.headers.get('x-notion-signature') || '';
  const expected = 'sha256=' + crypto.createHmac('sha256', secret).update(raw).digest('hex');
  if (!secret || sig.length !== expected.length ||
      !crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected))) {
    return NextResponse.json({ ok: false, error: 'bad signature' }, { status: 401 });
  }
  if (isDeployed()) {
    return NextResponse.json({ ok: true, queued: false, note: 'deployed: picked up by the daily freshness check' }, { status: 202 });
  }
  const t = (new URL(req.url).searchParams.get('tenant') || 'vanna').toLowerCase();
  if (!TENANT.test(t)) return NextResponse.json({ ok: false, error: 'bad tenant' }, { status: 400 });
  const r = await runPython(['-m', 'pipeline.brand_brain.notion_sync', 'dirty', t], 30_000);
  return NextResponse.json({ ok: r.ok, marked: r.ok, tenant: t }, { status: r.ok ? 200 : 500 });
}
