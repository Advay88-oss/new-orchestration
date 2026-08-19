import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const LEDGER_PATH = path.resolve('D:/new orchestration/pipeline/state/spend-ledger.json');

export async function GET() {
  try {
    if (!fs.existsSync(LEDGER_PATH)) {
      return NextResponse.json({
        spent_usd: 0.0,
        calls: 0,
        input_tokens: 0,
        output_tokens: 0,
        started: new Date().toISOString(),
        cap_usd: 10.0,
        remaining_usd: 10.0
      });
    }

    const raw = fs.readFileSync(LEDGER_PATH, 'utf-8');
    const data = JSON.parse(raw);
    
    // Explicitly add cap_usd and calculate remaining_usd as per the API contract
    const cap_usd = 10.0;
    const spent_usd = data.spent_usd ?? 0.0;
    const remaining_usd = Math.max(0.0, cap_usd - spent_usd);

    return NextResponse.json({
      spent_usd,
      calls: data.calls ?? 0,
      input_tokens: data.input_tokens ?? 0,
      output_tokens: data.output_tokens ?? 0,
      started: data.started ?? new Date().toISOString(),
      cap_usd,
      remaining_usd
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
