import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

/** Liveness for the uptime check and the hourly watch. Says nothing else. */
export async function GET() {
  return NextResponse.json({ ok: true, at: new Date().toISOString() }, { headers: { 'Cache-Control': 'no-store' } });
}
