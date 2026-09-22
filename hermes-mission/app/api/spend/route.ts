import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const PROXY_URL = 'http://127.0.0.1:8900/_spend';
const LEDGER_PATH = path.resolve('D:/new orchestration/pipeline/state/spend-ledger.json');

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    // 1. First attempt: Query live spend proxy on :8900
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 1500);

      const res = await fetch(PROXY_URL, {
        cache: 'no-store',
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (res.ok) {
        const liveData = await res.json();
        const cap_usd = liveData.cap_usd ?? 10.0;
        const spent_usd = liveData.spent_usd ?? 0.0;
        const remaining_usd = liveData.remaining_usd ?? Math.max(0, cap_usd - spent_usd);

        const payload = {
          spent_usd,
          cap_usd,
          remaining_usd,
          calls: liveData.calls ?? 0,
          input_tokens: liveData.input_tokens ?? 0,
          output_tokens: liveData.output_tokens ?? 0,
          started: liveData.started ?? '2026-09-19T00:00:00Z',
          source: 'LIVE_PROXY_8900'
        };

        // Sync to spend-ledger.json so file remains up to date
        try {
          fs.writeFileSync(LEDGER_PATH, JSON.stringify(payload, null, 2), 'utf-8');
        } catch {}

        return NextResponse.json(payload);
      }
    } catch (proxyErr) {
      // Proxy temporarily offline or timeout, proceed to fallback
    }

    // 2. Fallback: Read local spend-ledger.json
    if (fs.existsSync(LEDGER_PATH)) {
      const raw = fs.readFileSync(LEDGER_PATH, 'utf-8');
      const data = JSON.parse(raw);
      const cap_usd = data.cap_usd ?? 10.0;
      const spent_usd = data.spent_usd ?? 0.0;
      const remaining_usd = Math.max(0, cap_usd - spent_usd);

      return NextResponse.json({
        spent_usd,
        cap_usd,
        remaining_usd,
        calls: data.calls ?? 0,
        input_tokens: data.input_tokens ?? 0,
        output_tokens: data.output_tokens ?? 0,
        started: data.started ?? '2026-09-19T00:00:00Z',
        source: 'LOCAL_LEDGER_SYNC'
      });
    }

    // 3. Fail-safe default matching current live telemetry
    return NextResponse.json({
      spent_usd: 0.0,
      cap_usd: 10.0,
      remaining_usd: 10.0,
      calls: 0,
      input_tokens: 0,
      output_tokens: 0,
      started: '2026-09-19T00:00:00Z',
      source: 'DEFAULT_TELEMETRY'
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
