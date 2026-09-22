import { NextResponse } from 'next/server';
import { manifest } from '@/lib/v2';

export const dynamic = 'force-dynamic';

/**
 * Stage identities, derived from the manifest.
 *
 * This route returned a hardcoded pubkey->agent map for the previous thirteen
 * agents (agent-01-intelligence-scout, ...). Those names no longer correspond
 * to anything the pipeline runs, and the "pubkeys" were decorative strings —
 * there is no relay and no keypair behind them.
 */
export async function GET() {
  const stages = manifest();
  const out: Record<string, string> = {};
  for (const s of stages) out[s.stage] = `${s.kind}: ${s.purpose}`;
  return NextResponse.json(out);
}
