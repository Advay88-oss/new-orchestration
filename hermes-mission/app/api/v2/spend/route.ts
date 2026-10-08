import { NextResponse } from 'next/server';
import { ownerOnly } from '@/lib/local-only';
import { gtmSpend } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

/** Spend across the 13 GTM agents' cycles (was: the `core/` pipeline's). */
export async function GET() {
  const denied = ownerOnly('the v2 pipeline');
  if (denied) return denied;
  return NextResponse.json(await gtmSpend());
}
