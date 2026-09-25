'use client';

/**
 * The 13 GTM agents — ARCHITECTURE.md Agent 01-13.
 *
 * The dashboard previously showed the `core/` pipeline's thirteen stages under
 * the heading "13 GTM Agents". Those are a different system; the founder's own
 * agents (`pipeline/gtm_*`) had no view at all.
 *
 * Every value is read from the run journal that `autonomous_cycle.py` writes.
 * Two things this deliberately does NOT do:
 *
 *   - It does not draw a mid-run agent as a failure. The first version showed
 *     A09 as `never_ran` in alarm-red while the cycle was still four agents
 *     away from reaching it, which reads as a crash rather than a queue.
 *   - It does not pad deterministic agents with fake token counts. Five of the
 *     thirteen legitimately call no model; their cards say so.
 */

import React, { useCallback, useEffect, useState } from 'react';
import { MONO } from '@/lib/colors';
import { AGENTS as AGENT_DEFS, AGENT_COUNT, LEARNING_COUNT } from '@/lib/agents';

const ACCENT = '#A98CFF';
const DIM = '#6C6C6C';
const FAINT = '#3A3A42';
const LEARN = '#4ADE9B';

const MODEL_TONE: Record<string, string> = {
  'gemini-3.8-flash': '#A98CFF',
  'gemini-3.1-flash-image': '#38C9EF',
  'gemini-3-pro-image': '#F5A524',
  'veo-3.1-generate-001': '#FF7AB6',
};

/** The four operational tracks from ARCHITECTURE.md; members come from lib/agents. */
const TRACKS: { name: string; blurb: string; ids: string[] }[] = [
  { key: 'intelligence', name: 'Intelligence & Strategy',
    blurb: 'Finds what is happening and decides whether Vanna has an answer' },
  { key: 'creative', name: 'Creative & Media',
    blurb: 'Writes the post, directs and renders the poster and the video, and judges them' },
  { key: 'governance', name: 'Governance & Distribution',
    blurb: 'Blocks what should not ship; dispatch waits for a human. Fixed by design' },
  { key: 'learning', name: 'Learning',
    blurb: 'Turns founder decisions and run outcomes into what every agent reads next' },
].map((t) => ({ ...t, ids: AGENT_DEFS.filter((a) => a.track === t.key).map((a) => a.id) }));

interface Agent {
  n: number; id: string; code: string; name: string; role: string;
  learns: string | null; fixed: string | null;
  model: string | null; kind: 'MODEL_BACKED' | 'DETERMINISTIC';
  status: string; detail: string; outputs: string[]; at: string | null;
  modelCalls: number; modelCallsOk: number;
  inputTokens: number; outputTokens: number; durationS: number;
}

interface Payload {
  runId: string | null; agents: Agent[]; declared: number;
  modelBacked: number; ranThisRun: number; failed: string[];
  modelsUsed: string[]; status: string | null;
}

export function GtmAgents() {
  const [data, setData] = useState<Payload | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch('/api/gtm/agents', { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
      setErr(null);
    } catch (e: any) {
      setErr(String(e?.message || e));
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 8000);
    return () => clearInterval(t);
  }, [load]);

  if (err) return <Note tone="#F0666B">Could not read agent status: {err}</Note>;
  if (!data) return <Note tone={DIM}>Loading…</Note>;

  const byId = new Map(data.agents.map((a) => [a.id, a]));
  const running = data.status === 'running' || data.status === null
    ? data.agents.some((a) => a.status !== 'never_ran') &&
      data.agents.some((a) => a.status === 'never_ran')
    : false;

  // Mid-run, the agents after the current one have not failed — they are
  // queued. Find the frontier so they can be drawn as pending.
  const lastActive = data.agents.reduce(
    (acc, a, i) => (a.status !== 'never_ran' ? i : acc), -1);

  return (
    <div className="vanna-section">
      <header style={{ marginBottom: 22 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, flexWrap: 'wrap' }}>
          <h2 style={{ margin: 0, fontSize: 20, color: '#EDEDED', fontWeight: 600 }}>
            {AGENT_COUNT} GTM Agents
          </h2>
          <span style={{ fontFamily: MONO, fontSize: 11.5, color: DIM }}>
            {data.runId ?? 'no run yet'}
          </span>
          {running && (
            <span style={{ fontFamily: MONO, fontSize: 11, color: ACCENT }}>
              ● cycle in progress
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: 26, marginTop: 12, flexWrap: 'wrap' }}>
          <Stat v={`${data.ranThisRun}/${data.declared}`} l="ran this cycle" />
          <Stat v={String(data.modelBacked)} l="model-backed" />
          <Stat v={`${LEARNING_COUNT}/${AGENT_COUNT}`} l="learning" tone={LEARN} />
          <Stat v={String(data.failed.length)} l="failed"
                tone={data.failed.length ? '#F0666B' : undefined} />
        </div>

        {data.modelsUsed.length > 0 && (
          <div style={{ display: 'flex', gap: 7, marginTop: 14, flexWrap: 'wrap' }}>
            {data.modelsUsed.map((m) => (
              <span key={m} style={{
                fontFamily: MONO, fontSize: 10.5, padding: '3px 9px', borderRadius: 4,
                color: MODEL_TONE[m] || ACCENT,
                border: `1px solid ${(MODEL_TONE[m] || ACCENT)}40`,
                background: `${(MODEL_TONE[m] || ACCENT)}0F`,
              }}>{m}</span>
            ))}
          </div>
        )}
      </header>

      {TRACKS.map((track) => (
        <section key={track.name} style={{ marginBottom: 26 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 10 }}>
            <h3 style={{
              margin: 0, fontFamily: MONO, fontSize: 11, color: '#B9B9C4',
              textTransform: 'uppercase', letterSpacing: 1,
            }}>{track.name}</h3>
            <span style={{ fontSize: 11.5, color: FAINT }}>{track.blurb}</span>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(268px, 1fr))',
            gap: 10,
          }}>
            {track.ids.map((id) => {
              const a = byId.get(id);
              if (!a) return null;
              const idx = data.agents.findIndex((x) => x.id === id);
              const pending = a.status === 'never_ran' && idx > lastActive && lastActive >= 0;
              return <Card key={id} a={a} pending={pending} runId={data.runId} />;
            })}
          </div>
        </section>
      ))}
    </div>
  );
}

function Card({ a, pending, runId }: { a: Agent; pending: boolean; runId: string | null }) {
  // An agent that should have reasoned but recorded no call is not healthy,
  // even when its stage returned ok.
  const silent = a.kind === 'MODEL_BACKED' && a.status === 'ok' && a.modelCalls === 0;

  const tone =
    pending ? FAINT
      : silent ? '#F5A524'
      : a.status === 'ok' ? '#4ADE9B'
      : a.status === 'degraded' ? '#F5A524'
      : a.status === 'failed' ? '#F0666B'
      : a.status === 'skipped' ? '#5A5A66'
      : FAINT;

  const label =
    pending ? 'queued'
      : silent ? 'ok · no model call'
      : a.status === 'never_ran' ? 'not run'
      : a.status;

  return (
    <article style={{
      border: `1px solid ${tone}2E`,
      borderLeft: `2px solid ${tone}`,
      borderRadius: 6,
      padding: '11px 13px 12px',
      background: '#0C0716',
      opacity: pending ? 0.5 : 1,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'baseline' }}>
        <span style={{ fontFamily: MONO, fontSize: 10.5, color: DIM }}>
          {a.code}
        </span>
        <span style={{ fontFamily: MONO, fontSize: 10.5, color: tone }}>{label}</span>
      </div>

      <h4 style={{ margin: '5px 0 7px', fontSize: 13.5, color: '#E8E8ED', fontWeight: 600, lineHeight: 1.3 }}>
        {a.name}
      </h4>

      {a.kind === 'DETERMINISTIC' ? (
        <div style={{ fontFamily: MONO, fontSize: 10.5, color: FAINT }}>
          deterministic · no model by design
        </div>
      ) : (
        <div style={{ fontFamily: MONO, fontSize: 10.5, lineHeight: 1.65 }}>
          <div style={{ color: MODEL_TONE[a.model || ''] || ACCENT }}>{a.model}</div>
          {a.modelCalls > 0 ? (
            <div style={{ color: '#8A8A93' }}>
              {a.modelCallsOk}/{a.modelCalls} calls
              {a.inputTokens > 0 &&
                ` · ${(a.inputTokens / 1000).toFixed(1)}k in / ${(a.outputTokens / 1000).toFixed(1)}k out`}
              {a.durationS > 0 && ` · ${a.durationS}s`}
            </div>
          ) : (
            <div style={{ color: FAINT }}>{pending ? 'waiting its turn' : 'no calls recorded'}</div>
          )}
        </div>
      )}

      <div style={{ fontSize: 11, marginTop: 7, lineHeight: 1.45,
                    color: a.learns ? '#9FE3BF' : '#6E6E78' }}>
        <span style={{ fontFamily: MONO, fontSize: 9.5, letterSpacing: 0.6, marginRight: 6,
                       color: a.learns ? LEARN : '#5A5A66' }}>
          {a.learns ? 'LEARNS' : 'FIXED'}
        </span>
        {a.learns || a.fixed}
      </div>

      {a.detail && !pending && (
        <div style={{ fontSize: 11, color: '#6E6E78', marginTop: 6, lineHeight: 1.45 }}>
          {a.detail.length > 150 ? a.detail.slice(0, 150) + '…' : a.detail}
        </div>
      )}

      {runId && a.outputs.length > 0 && (
        <div style={{ marginTop: 9, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {a.id === 'A08_visual_synthesis' && (
            <>
              <Link href={`/api/gtm/artifact/${runId}/visual`}>visual</Link>
              <Link href={`/api/gtm/artifact/${runId}/meme`}>meme</Link>
            </>
          )}
          {a.id === 'A09_video_production' && (
            <Link href={`/api/gtm/artifact/${runId}/video`}>play video</Link>
          )}
        </div>
      )}
    </article>
  );
}

function Link({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a href={href} target="_blank" rel="noreferrer" style={{
      fontFamily: MONO, fontSize: 10.5, color: ACCENT, textDecoration: 'none',
      border: `1px solid ${ACCENT}3A`, borderRadius: 4, padding: '2px 8px',
    }}>{children}</a>
  );
}

function Stat({ v, l, tone }: { v: string; l: string; tone?: string }) {
  return (
    <div>
      <div style={{ fontFamily: MONO, fontSize: 19, color: tone || '#EDEDED', lineHeight: 1.1 }}>{v}</div>
      <div style={{ fontFamily: MONO, fontSize: 9.5, color: DIM, textTransform: 'uppercase', letterSpacing: 0.7 }}>{l}</div>
    </div>
  );
}

function Note({ tone, children }: { tone: string; children: React.ReactNode }) {
  // Same gutter as the loaded view, so a loading or error state does not sit
  // flush against the sidebar either.
  return (
    <div className="vanna-section" style={{ color: tone, fontFamily: MONO, fontSize: 13 }}>
      {children}
    </div>
  );
}
