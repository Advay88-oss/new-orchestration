import fixture from './fixture.json';
import type { ArcId, MissionData, NostrMessage, Run, StageId, VertexCall } from './types';

/** Single seam between the UI and where data comes from.
 *
 *  Today: a captured fixture whose shapes match the real sources exactly.
 *  Tomorrow: swap `source` to 'live' and implement the three fetches below.
 *  Nothing above this file should know which one is in use. */
export const MISSION = fixture as unknown as MissionData;

export const source: 'fixture' | 'live' = 'fixture';

export const AGENT_IDS = MISSION.AGENTS.map((a) => a.id);

export function agentForPubkey(pubkey: string): string {
  return MISSION.AGENT_BY_KEY[pubkey] ?? pubkey.slice(0, 8);
}

export function arcOf(agentId: string): ArcId | null {
  if (agentId.startsWith('strategist-')) {
    return agentId.replace('strategist-', '') as ArcId;
  }
  return null;
}

export function arcColour(arc: ArcId | null): string {
  return arc ? `var(--arc-${arc})` : 'var(--ink-3)';
}

export function runById(key: string): Run | undefined {
  return MISSION.RUNS.find((r) => r.key === key);
}

export function runCost(run: Run): number {
  return run.calls.reduce((sum, c) => sum + c.cost_usd, 0);
}

export function totalSpent(): number {
  return MISSION.RUNS.reduce((sum, r) => sum + runCost(r), 0);
}

export function costByAgent(run: Run): { agent: string; cost: number; calls: number }[] {
  const map = new Map<string, { cost: number; calls: number }>();
  for (const c of run.calls) {
    const cur = map.get(c.agent) ?? { cost: 0, calls: 0 };
    cur.cost += c.cost_usd;
    cur.calls += 1;
    map.set(c.agent, cur);
  }
  return [...map.entries()]
    .map(([agent, v]) => ({ agent, ...v }))
    .sort((a, b) => b.cost - a.cost);
}

export function costByStage(run: Run): { stage: StageId; cost: number }[] {
  const map = new Map<StageId, number>();
  for (const c of run.calls) map.set(c.stage, (map.get(c.stage) ?? 0) + c.cost_usd);
  return MISSION.STAGE_ORDER.filter((s) => map.has(s)).map((s) => ({
    stage: s,
    cost: map.get(s)!,
  }));
}

export function tokenSplit(calls: VertexCall[]) {
  let cached = 0;
  let fresh = 0;
  let output = 0;
  for (const c of calls) {
    const cachedTokens = c.usage.cachedContentTokenCount ?? 0;
    cached += cachedTokens;
    fresh += Math.max(0, c.usage.promptTokenCount - cachedTokens);
    output += c.usage.candidatesTokenCount + (c.usage.thoughtsTokenCount ?? 0);
  }
  return { cached, fresh, output };
}

/** Which agent a message replies to, if the tags say so. Returns null when the
 *  thread parent is unknown — guessing would fabricate a conversation. */
export function parentOf(msg: NostrMessage): string | null {
  const e = msg.tags.find((t) => t[0] === 'e');
  return e ? e[1] : null;
}

/** A reply from one strategist to another. This is the number that says whether
 *  a debate happened or three monologues did. */
export function crossReplies(run: Run): { count: number; pairs: number } {
  const byId = new Map(run.messages.map((m) => [m.id, m]));
  const pairs = new Set<string>();
  let count = 0;
  for (const m of run.messages) {
    const parentId = parentOf(m);
    if (!parentId) continue;
    const parent = byId.get(parentId);
    if (!parent) continue;
    const from = agentForPubkey(m.pubkey);
    const to = agentForPubkey(parent.pubkey);
    if (from === to) continue;
    if (!from.startsWith('strategist-') || !to.startsWith('strategist-')) continue;
    count += 1;
    pairs.add([from, to].sort().join('|'));
  }
  return { count, pairs: pairs.size };
}

/** Try to read an embedded JSON payload out of message text. Returns the raw
 *  text on failure so the caller can show it — a message that will not parse is
 *  still evidence and must never be dropped. */
export function parsePayload(content: string):
  | { ok: true; data: unknown }
  | { ok: false; error: string } {
  const fenced = content.match(/```(?:json)?\s*([\s\S]*?)```/);
  const candidate = fenced ? fenced[1] : content.slice(content.indexOf('{'));
  try {
    return { ok: true, data: JSON.parse(candidate) };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : String(e) };
  }
}

export const fmt = {
  usd(n: number, dp = 4): string {
    return `$${n.toFixed(dp)}`;
  },
  tokens(n: number): string {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
    return String(n);
  },
  /** Local time for reading, UTC kept for the tooltip. */
  time(unixSeconds: number): string {
    return new Date(unixSeconds * 1000).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  },
  utc(unixSeconds: number): string {
    return new Date(unixSeconds * 1000).toISOString().replace('.000', '');
  },
  date(unixSeconds: number): string {
    return new Date(unixSeconds * 1000).toLocaleDateString([], {
      day: '2-digit',
      month: 'short',
    });
  },
  duration(from: number, to: number | null): string {
    if (to == null) return '—';
    const s = Math.max(0, to - from);
    if (s < 60) return `${s}s`;
    const m = Math.floor(s / 60);
    const rem = s % 60;
    if (m < 60) return rem ? `${m}m ${rem}s` : `${m}m`;
    return `${Math.floor(m / 60)}h ${m % 60}m`;
  },
};
