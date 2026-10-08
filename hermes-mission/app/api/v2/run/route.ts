import { NextResponse } from 'next/server';
import { ownerOnly } from '@/lib/local-only';
import { enqueue, queueCounts, workerHealth } from '@/lib/v2';

export const dynamic = 'force-dynamic';

export async function POST(req: Request) {
  const denied = ownerOnly('the v2 pipeline');
  if (denied) return denied;
  let directive = '';
  try {
    directive = (await req.json())?.directive ?? '';
  } catch {
    /* empty body means an auto-pick run */
  }

  const job = enqueue(directive);
  const worker = workerHealth();
  return NextResponse.json({
    ok: true,
    job: job.id,
    queued: queueCounts(),
    // Say plainly when nothing will pick this up, instead of implying it started.
    worker,
    note: worker.alive
      ? 'queued; a worker is running and will claim it'
      : 'queued, but NO WORKER IS RUNNING — start one: python -m core.worker',
  });
}

export async function GET() {
  const denied = ownerOnly('the v2 pipeline');
  if (denied) return denied;
  return NextResponse.json({ queued: queueCounts(), worker: workerHealth() });
}
