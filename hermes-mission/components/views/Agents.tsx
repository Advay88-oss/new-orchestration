'use client';

/**
 * Stage cards, from the run journal.
 *
 * What this replaces: 489 lines in which every agent's name, engine string,
 * "core responsibility", input sources and output description were written by
 * hand — "Intelligence Scout & Parallel Stream Daemon", "Multi-Source
 * ThreadPool (Python + Horizon + DeFiLlama)", "CONNECTED & POLLING (Every
 * 30m)", "Blend v2 ($149.7M)" — with `|| 18.5` style fallbacks so a missing
 * measurement still rendered a plausible number. The header said "Zero mock
 * data" directly above it.
 *
 * Every field below comes from /api/agents/status, which derives from the
 * manifest and the newest run's journal. Where a run recorded nothing, the card
 * says so rather than filling the gap.
 */

import React, { useCallback, useEffect, useState } from 'react';
import { MONO } from '@/lib/colors';

const ACCENT = '#A387FF';

const STATE_TONE: Record<string, string> = {
  succeeded: '#38EF7D',
  degraded: '#F5A524',
  failed: '#FC5457',
  running: ACCENT,
  not_reached: '#4A4A4A',
  never_run: '#4A4A4A',
};

interface AgentCard {
  id: string;
  n: number;
  role: string;
  kind: 'AGENT' | 'STAGE';
  status: string;
  last_run: string | null;
  model: string | null;
  prompt_version: string | null;
  input_tokens: number;
  output_tokens: number;
  duration_s: number | null;
  tool_calls: string[];
  degraded_reason: string | null;
  error: string | null;
  reasoned: boolean | null;
}

const label: React.CSSProperties = {
  fontSize: 9, letterSpacing: '.12em', color: '#6A6A6A', textTransform: 'uppercase',
};

export function Agents() {
  const [data, setData] = useState<{
    agents: AgentCard[]; declared_agents: number;
    agents_that_reasoned: number; source_run: string | null;
  } | null>(null);
  const [filter, setFilter] = useState<'all' | 'AGENT' | 'STAGE'>('all');
  const [err, setErr] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [scanMsg, setScanMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const r = await fetch('/api/agents/status', { cache: 'no-store' });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setData(await r.json());
      setErr(null);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [load]);

  async function scan() {
    setScanning(true);
    setScanMsg(null);
    try {
      const r = await fetch('/api/scout', { method: 'POST' });
      const j = await r.json();
      setScanMsg(j.success ? 'Scan complete.' : `Scan failed: ${j.error ?? 'unknown'}`);
    } catch (e: any) {
      setScanMsg(`Scan failed: ${e?.message ?? e}`);
    } finally {
      setScanning(false);
      load();
    }
  }

  if (err) {
    return (
      <section className="vanna-card" style={{ borderColor: '#5E0D46' ,  }}>
        <div style={{ color: '#FC5457', fontSize: 13 }}>
          Backend unreachable: {err}. This view has no fixtures to fall back to.
        </div>
      </section>
    );
  }
  if (!data) {
    return <section className="vanna-card"><div style={{ color: '#7A7A7A', fontSize: 13 }}>Loading…</div></section>;
  }

  const shown = data.agents.filter((a) => filter === 'all' || a.kind === filter);

  return (
    <section className="vanna-section" style={{ padding: 0 }}>
      <div className="vanna-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
          <span style={{ width: 8, height: 8, borderRadius: 999, background: '#38EF7D' }} />
          <span style={{ fontFamily: MONO, fontSize: 11.5, color: '#38EF7D', letterSpacing: '.07em' }}>
            {data.source_run ? `SOURCE RUN ${data.source_run}` : 'NO RUN RECORDED'}
          </span>
        </div>
        <h2 style={{ fontSize: 20, fontWeight: 700, margin: '10px 0 0', color: '#EDEDED' }}>
          {data.agents.length} pipeline stages
        </h2>
        <p style={{ fontSize: 12.5, color: '#7A7A7A', marginTop: 6, lineHeight: 1.5, maxWidth: 720 }}>
          {data.declared_agents} are declared agents; {data.agents_that_reasoned} of them recorded a
          real model call in this run. A stage with no run behind it is shown as never run, not as
          connected.
        </p>

        <div style={{ display: 'flex', gap: 8, marginTop: 14, flexWrap: 'wrap' }}>
          <button
            onClick={scan}
            disabled={scanning}
            style={{
              padding: '8px 16px', borderRadius: 8, border: 'none', fontSize: 12, fontWeight: 700,
              background: scanning ? '#2A2A2A' : ACCENT, color: scanning ? '#7A7A7A' : '#07020D',
              cursor: scanning ? 'default' : 'pointer', fontFamily: MONO,
            }}
          >
            {scanning ? 'Scanning…' : 'Run live market scan'}
          </button>
          {(['all', 'AGENT', 'STAGE'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: '8px 14px', borderRadius: 8, fontSize: 11.5, cursor: 'pointer',
                fontFamily: MONO, letterSpacing: '.05em',
                border: `1px solid ${filter === f ? ACCENT : '#232323'}`,
                background: filter === f ? '#17132A' : '#0D0D0D', color: '#EDEDED',
              }}
            >
              {f === 'all' ? `ALL ${data.agents.length}` : f}
            </button>
          ))}
        </div>
        {scanMsg && (
          <p style={{ fontSize: 11.5, color: scanMsg.startsWith('Scan failed') ? '#FC5457' : '#7A7A7A', marginTop: 9 }}>
            {scanMsg}
          </p>
        )}
      </div>

      {shown.map((a) => {
        const tone = STATE_TONE[a.status] ?? '#4A4A4A';
        return (
          <div key={a.id} className="vanna-card" style={{ borderLeft: `2px solid ${tone}` }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 11, flexWrap: 'wrap' }}>
              <span style={{
                fontFamily: MONO, fontSize: 10.5, padding: '4px 9px', borderRadius: 6,
                background: a.kind === 'AGENT' ? '#241C3A' : '#1A1A1A',
                color: a.kind === 'AGENT' ? ACCENT : '#8A8A8A', letterSpacing: '.06em',
              }}>
                {String(a.n).padStart(2, '0')} · {a.kind}
              </span>
              <span style={{ fontSize: 15, fontWeight: 700, color: '#EDEDED' }}>{a.id}</span>
              <span style={{
                marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 7,
                fontFamily: MONO, fontSize: 11, color: tone, letterSpacing: '.06em',
              }}>
                <span style={{ width: 7, height: 7, borderRadius: 999, background: tone }} />
                {a.status.toUpperCase()}
              </span>
            </div>

            <div style={{ fontSize: 12.5, color: '#9A9A9A', marginTop: 8, lineHeight: 1.5 }}>
              {a.role}
            </div>

            <div style={{
              display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(170px,1fr))',
              gap: 10, marginTop: 14,
            }}>
              <Cell title="Model" value={a.model ?? '—'} mono
                    note={a.kind === 'AGENT' && a.reasoned === false ? 'no model call recorded' : undefined} />
              <Cell title="Prompt version" value={a.prompt_version ?? '—'} mono />
              <Cell title="Tokens" value={a.input_tokens || a.output_tokens
                ? `${a.input_tokens.toLocaleString()} / ${a.output_tokens.toLocaleString()}` : '—'} mono />
              <Cell title="Duration" value={a.duration_s != null ? `${a.duration_s}s` : '—'} mono />
              <Cell title="Tools" value={a.tool_calls?.length ? a.tool_calls.join(', ') : '—'} />
            </div>

            {a.degraded_reason && (
              <div style={{
                marginTop: 12, padding: '9px 11px', borderRadius: 8,
                background: '#1A1408', border: '1px solid #3A2A08', color: '#F5A524', fontSize: 12,
                lineHeight: 1.5,
              }}>
                {a.degraded_reason}
              </div>
            )}
            {a.error && (
              <div style={{
                marginTop: 10, padding: '9px 11px', borderRadius: 8,
                background: '#1E0A0A', border: '1px solid #4A1414', color: '#FC5457', fontSize: 12,
              }}>
                {a.error}
              </div>
            )}
          </div>
        );
      })}
    </section>
  );
}

function Cell({ title, value, mono, note }: {
  title: string; value: string; mono?: boolean; note?: string;
}) {
  return (
    <div style={{ border: '1px solid #1C1C1C', borderRadius: 8, padding: '9px 11px' }}>
      <div style={label}>{title}</div>
      <div style={{
        fontSize: 12.5, color: '#EDEDED', marginTop: 4, wordBreak: 'break-word',
        fontFamily: mono ? MONO : undefined,
      }}>
        {value}
      </div>
      {note && <div style={{ fontSize: 10.5, color: '#FC5457', marginTop: 4 }}>{note}</div>}
    </div>
  );
}
