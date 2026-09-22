import { NextResponse } from 'next/server';
import { gtmRuns } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

export async function GET(req: Request) {
  const limit = Number(new URL(req.url).searchParams.get('limit') || 15);
  return NextResponse.json({ runs: gtmRuns(limit) });
}
