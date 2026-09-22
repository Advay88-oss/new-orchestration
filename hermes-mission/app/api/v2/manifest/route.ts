import { NextResponse } from 'next/server';
import { gtmManifest } from '@/lib/gtm';

export const dynamic = 'force-dynamic';

/** The 13 GTM agents (was: the `core/` pipeline's 13 stages). */
export async function GET() {
  return NextResponse.json({ stages: gtmManifest() });
}
