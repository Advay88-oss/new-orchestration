import { NextResponse } from 'next/server';
import { runReasoning, runView } from '@/lib/v2';

export const dynamic = 'force-dynamic';

export async function GET(_req: Request, { params }: { params: { id: string } }) {
  const run = runView(params.id);
  if (!run) return NextResponse.json({ error: `no journal for ${params.id}` }, { status: 404 });
  return NextResponse.json({ runId: run.runId, directive: run.directive, ...runReasoning(params.id) });
}
