import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { NextResponse } from 'next/server';
import { getText, isDeployed, putBytes } from '@/lib/gcs';
import { companyAccess } from '@/lib/local-only';
import { allow, clientIp } from '@/lib/ratelimit';
import { REPO_ROOT } from '@/lib/v2';

export const dynamic = 'force-dynamic';

/**
 * The Studio: posters the visual agents made (pipeline/gtm_creative/studio.py).
 *
 *   GET            the list (index.json: locally from disk, deployed from the bucket)
 *   GET ?job=<id>  one Assistant image job: running, done (with the new poster) or failed
 *   POST           an image the owner attaches in the chat (multipart `file`) -> {file}
 *
 * Files are served by /api/media?file=<name> like every other poster.
 */
const STUDIO = path.join(REPO_ROOT, 'pipeline', 'state', 'studio');
const JOB = /^v_[a-z0-9]{10}$/;
const TYPES: Record<string, string> = { 'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp' };
const MAX_BYTES = 15 * 1024 * 1024;

function readLocal(file: string): string | null {
  try { return fs.readFileSync(file, 'utf-8'); } catch { return null; }
}

export async function GET(req: Request) {
  const job = new URL(req.url).searchParams.get('job');
  if (job !== null) {
    if (!JOB.test(job)) return NextResponse.json({ ok: false, error: 'bad job id' }, { status: 400 });
    // The job runs in this container and writes its status here; the bucket copy outlives a restart.
    const raw = readLocal(path.join(STUDIO, 'jobs', job + '.json'))
      ?? (isDeployed() ? await getText('studio/jobs/' + job + '.json') : null);
    if (!raw) return NextResponse.json({ ok: false, error: 'no such job' }, { status: 404 });
    try { return NextResponse.json({ ok: true, job: JSON.parse(raw) }); } catch {
      return NextResponse.json({ ok: false, error: 'the job is being written' }, { status: 503 });
    }
  }
  const raw = isDeployed() ? await getText('studio/index.json') : readLocal(path.join(STUDIO, 'index.json'));
  let items: unknown[] = [];
  try { items = raw ? (JSON.parse(raw).items || []) : []; } catch { items = []; }
  return NextResponse.json({ ok: true, items }, { headers: { 'Cache-Control': 'no-store' } });
}

export async function POST(req: Request) {
  const access = companyAccess('uploading an image', null, { write: true, publicChat: true });
  if (access instanceof NextResponse) return access;
  if (!allow('studio-upload:' + clientIp(req), 40, 3_600_000)) {
    return NextResponse.json({ ok: false, error: 'too many uploads this hour' }, { status: 429 });
  }
  let form: FormData;
  try { form = await req.formData(); } catch {
    return NextResponse.json({ ok: false, error: 'send the image as a file' }, { status: 400 });
  }
  const f = form.get('file');
  if (!f || typeof f === 'string') return NextResponse.json({ ok: false, error: 'no file' }, { status: 400 });
  const ext = TYPES[f.type];
  if (!ext) return NextResponse.json({ ok: false, error: 'PNG, JPEG or WebP only' }, { status: 400 });
  if (f.size > MAX_BYTES) return NextResponse.json({ ok: false, error: 'the image is over 15 MB' }, { status: 413 });
  const body = Buffer.from(await f.arrayBuffer());
  // The bytes must be what the type says (the browser's type is only a claim).
  const sig = body.subarray(0, 12);
  const real = sig[0] === 0x89 && sig[1] === 0x50 ? 'png'
    : sig[0] === 0xff && sig[1] === 0xd8 ? 'jpg'
    : sig.subarray(0, 4).toString() === 'RIFF' && sig.subarray(8, 12).toString() === 'WEBP' ? 'webp' : '';
  if (real !== ext) return NextResponse.json({ ok: false, error: 'that file is not a real image' }, { status: 400 });
  const file = 'studio-up-' + crypto.randomBytes(6).toString('hex') + '.' + ext;
  try {
    fs.mkdirSync(STUDIO, { recursive: true });
    fs.writeFileSync(path.join(STUDIO, file), body);
  } catch (e: any) {
    if (!isDeployed()) return NextResponse.json({ ok: false, error: 'could not save: ' + String(e?.message || e) }, { status: 500 });
  }
  if (isDeployed() && !(await putBytes('studio/' + file, body, f.type))) {
    return NextResponse.json({ ok: false, error: 'could not store the image' }, { status: 502 });
  }
  return NextResponse.json({ ok: true, file, url: '/api/media?file=' + file });
}
