import { NextResponse } from 'next/server';
import { gtmReferences } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

/**
 * Vanna References: every live item A01 scraped (posts, docs, news, market
 * data) with its source link, joined to A02's reading of it — the grade, the
 * one move Vanna can make, and the strategies that cite it.
 *
 * `?runId=` selects a run; without it the newest run with a harvest is used.
 */
export async function GET(req: Request) {
  const runId = new URL(req.url).searchParams.get('runId') || undefined;
  try {
    const refs = await gtmReferences(runId);
    if (!refs) {
      return NextResponse.json(
        { success: false, error: 'no harvest recorded yet — run a cycle' },
        { status: 404 },
      );
    }
    return NextResponse.json({ success: true, ...refs });
  } catch (err: any) {
    return NextResponse.json(
      { success: false, error: String(err?.message ?? err) },
      { status: 500 },
    );
  }
}
