import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const STATE = path.resolve('D:/new orchestration/pipeline/state');
const TRENDS = path.join(STATE, 'trends');
const FEED = path.join(STATE, 'live_run.jsonl');

export const dynamic = 'force-dynamic';

// Detect the tenant of the current/most-recent run so we show the right scout dump.
function currentTenant(): string {
  try {
    const first = fs
      .readFileSync(FEED, 'utf-8')
      .split('\n')
      .filter((l) => l.trim())
      .map((l) => {
        try {
          return JSON.parse(l);
        } catch {
          return null;
        }
      })
      .find((e) => e && e.tenant);
    if (first?.tenant) return String(first.tenant).toLowerCase();
  } catch {
    /* ignore */
  }
  return '';
}

export async function GET() {
  try {
    if (!fs.existsSync(TRENDS)) {
      return NextResponse.json({ ok: false, reason: 'no trends dir', items: [] });
    }
    const tenant = currentTenant();
    let files = fs
      .readdirSync(TRENDS)
      .filter((f) => f.endsWith('.json'))
      .map((f) => ({ f, m: fs.statSync(path.join(TRENDS, f)).mtimeMs }))
      .sort((a, b) => b.m - a.m);

    // Prefer the current tenant's newest dump; else the newest overall.
    let pick = tenant ? files.find((x) => x.f.toLowerCase().startsWith(tenant + '-')) : undefined;
    if (!pick) pick = files[0];
    if (!pick) return NextResponse.json({ ok: false, reason: 'no scout dumps', items: [] });

    const data = JSON.parse(fs.readFileSync(path.join(TRENDS, pick.f), 'utf-8'));
    const items = Array.isArray(data.items) ? data.items : [];

    // Relevance score: engagement percentile within this batch (0-100). The scout
    // ranks by engagement, so this exposes the same signal it ranked on.
    const engs = items.map((i: any) => Number(i.engagement) || 0);
    const maxEng = Math.max(1, ...engs);
    const scored = items.map((i: any) => ({
      channel: i.channel ?? 'web',
      keyword: i.keyword ?? '',
      title: i.title ?? '',
      url: i.url ?? '',
      published: i.published ?? '',
      source: i.source ?? '',
      engagement: Number(i.engagement) || 0,
      relevance: Math.round(((Number(i.engagement) || 0) / maxEng) * 100),
    }));

    // Platforms actually swept + what was monitored.
    const platforms = Array.from(new Set(scored.map((i: any) => i.channel)));

    return NextResponse.json({
      ok: true,
      tenant: data.tenant ?? tenant ?? 'vanna',
      bundle: data.bundle ?? '',
      gathered_at: data.gathered_at_utc ?? '',
      file: pick.f,
      monitored: {
        keywords: data.keywords ?? [],
        subreddits: data.subreddits ?? [],
        platforms,
      },
      counts: data.counts ?? {},
      items: scored,
    });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e.message, items: [] }, { status: 500 });
  }
}
