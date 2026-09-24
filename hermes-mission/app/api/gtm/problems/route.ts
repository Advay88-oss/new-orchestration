import { NextResponse } from 'next/server';
import { gtmProblems } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

export async function GET(req: Request) {
  const limit = Number(new URL(req.url).searchParams.get('limit') ?? 60);
  try {
    return NextResponse.json({ success: true, ...(await gtmProblems(limit)) });
  } catch (err: any) {
    return NextResponse.json(
      { success: false, error: String(err?.message ?? err) },
      { status: 500 },
    );
  }
}
