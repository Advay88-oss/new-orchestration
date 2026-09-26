import crypto from 'crypto';
import { NextResponse } from 'next/server';
import { runPython } from '@/lib/python';

export const dynamic = 'force-dynamic';

/**
 * Telegram's webhook: the review packet's Approve / Revise / Kill buttons and
 * the founder's replies (a revision note, a posted link), on GCP. Locally the
 * long-polling listener does the same (pipeline/gtm_os/feedback_listener.py);
 * a bot has one or the other, never both.
 *
 * Telegram sends the secret registered with setWebhook in a header; anything
 * without it is dropped. Only the founder's chat is acted on (the listener's
 * own check). Always 200: Telegram retries anything else, and a retried
 * button press is a duplicate decision.
 */
export async function POST(req: Request) {
  const want = process.env.TELEGRAM_WEBHOOK_SECRET || '';
  const got = req.headers.get('x-telegram-bot-api-secret-token') || '';
  if (!want || got.length !== want.length || !crypto.timingSafeEqual(Buffer.from(got), Buffer.from(want))) {
    return NextResponse.json({ ok: false }, { status: 401 });
  }
  const update = await req.text();
  if (update.length > 100_000) return NextResponse.json({ ok: true });
  await runPython(['-m', 'pipeline.gtm_os.cloud_job', 'telegram'], 50_000, update);
  return NextResponse.json({ ok: true });
}
