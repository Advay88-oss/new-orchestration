import { NextResponse } from 'next/server';
import { gtmLegacyRuns } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

export async function GET(req: Request) {
  const limit = Number(new URL(req.url).searchParams.get('limit') ?? 50);
  return NextResponse.json({ runs: await gtmLegacyRuns(Number.isFinite(limit) ? limit : 50) });
}
