import { NextResponse } from 'next/server';
import { ownerOnly } from '@/lib/local-only';
import { runView } from '@/lib/v2';

export const dynamic = 'force-dynamic';

export async function GET(_req: Request, { params }: { params: { id: string } }) {
  const denied = ownerOnly('the v2 pipeline');
  if (denied) return denied;
  const run = runView(params.id);
  if (!run) return NextResponse.json({ error: `no journal for run ${params.id}` }, { status: 404 });
  return NextResponse.json(run);
}
