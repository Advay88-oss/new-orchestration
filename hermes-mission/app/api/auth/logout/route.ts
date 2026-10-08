import { NextResponse } from 'next/server';
import { OWNER_COOKIE } from '@/lib/viewer';

export const dynamic = 'force-dynamic';

/** Ends this browser's owner session. */
export async function POST() {
  const res = NextResponse.json({ ok: true, owner: false });
  res.cookies.delete(OWNER_COOKIE);
  return res;
}
