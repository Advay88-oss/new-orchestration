import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const CALL_LOG_PATH = path.resolve('D:/new orchestration/pipeline/logs/vertex-calls.jsonl');

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const since = searchParams.get('since');
    const sinceTime = since ? new Date(since).getTime() : 0;

    if (!fs.existsSync(CALL_LOG_PATH)) {
      return NextResponse.json([]);
    }

    const raw = fs.readFileSync(CALL_LOG_PATH, 'utf-8');
    const lines = raw.split('\n').filter(l => l.trim() !== '');
    
    const calls = [];
    let seq = 1;

    for (const line of lines) {
      try {
        const item = JSON.parse(line);
        const itemTime = new Date(item.ts).getTime();

        if (sinceTime && itemTime <= sinceTime) {
          continue;
        }

        // Map fields to match the VertexCall interface in lib/types.ts
        const usage = item.usage ?? {
          promptTokenCount: 0,
          cachedContentTokenCount: 0,
          candidatesTokenCount: 0,
          thoughtsTokenCount: 0
        };

        calls.push({
          seq: seq++,
          ts: item.ts,
          stage: item.stage ?? 'research', // Map to valid StageId
          agent: item.agent ?? 'trend-scout',
          model: item.model,
          rewritten_from: item.rewritten_from ?? null,
          usage: {
            promptTokenCount: usage.promptTokenCount ?? 0,
            cachedContentTokenCount: usage.cachedContentTokenCount ?? 0,
            candidatesTokenCount: usage.candidatesTokenCount ?? 0,
            thoughtsTokenCount: usage.thoughtsTokenCount ?? 0
          },
          cost_usd: item.cost_usd ?? 0.0
        });
      } catch (e) {
        // Skip malformed JSONL lines
      }
    }

    return NextResponse.json(calls);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
