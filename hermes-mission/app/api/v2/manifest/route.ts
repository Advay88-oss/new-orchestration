import { NextResponse } from 'next/server';
import { ownerOnly } from '@/lib/local-only';
import { gtmManifest } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

/** The 13 GTM agents (was: the `core/` pipeline's 13 stages). */
export async function GET() {
  const denied = ownerOnly('the v2 pipeline');
  if (denied) return denied;
  return NextResponse.json({ stages: gtmManifest() });
}
