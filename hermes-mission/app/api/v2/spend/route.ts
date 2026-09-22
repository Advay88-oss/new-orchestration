import { NextResponse } from 'next/server';
import { gtmSpend } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

/** Spend across the 13 GTM agents' cycles (was: the `core/` pipeline's). */
export async function GET() {
  return NextResponse.json(gtmSpend());
}
