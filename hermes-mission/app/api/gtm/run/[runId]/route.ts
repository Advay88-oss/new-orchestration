import { NextResponse } from 'next/server';
import { gtmRunDetail } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

export async function GET(
  _req: Request,
  { params }: { params: { runId: string } },
) {
  const id = params.runId === 'latest' ? undefined : params.runId;
  const detail = await gtmRunDetail(id);
  if (!detail) return NextResponse.json({ error: 'no run found' }, { status: 404 });
  return NextResponse.json(detail);
}
