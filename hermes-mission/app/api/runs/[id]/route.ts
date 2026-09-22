import { NextResponse } from 'next/server';
import { gtmLegacyRun } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

export async function GET(
  _req: Request,
  { params }: { params: { id: string } },
) {
  const run = gtmLegacyRun(params.id);
  if (!run) return NextResponse.json({ error: 'run not found' }, { status: 404 });
  return NextResponse.json(run);
}
