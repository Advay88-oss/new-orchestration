'use client';

/**
 * The 13 GTM agents — ARCHITECTURE.md Agent 01-13.
 *
 * The dashboard previously showed the `core/` pipeline's thirteen stages under
 * the heading "13 GTM Agents". Those are a different system; the founder's own
 * agents (`pipeline/gtm_*`) had no view at all.
 *
 * Every value here comes from /api/gtm/agents, which reads the run journal
 * `pipeline/gtm_os/autonomous_cycle.py` writes. Two things it deliberately does
 * NOT do:
 *
 *   - It does not show a green tick for an agent that made no model call when
 *     one was expected. A MODEL_BACKED agent with zero calls is drawn amber.
 *   - It does not hide the deterministic agents or pad them with fake token
 *     counts. Four of the thirteen legitimately call no model; the card says
 *     "deterministic" rather than implying a silent failure.
 */

import React, { useCallback, useEffect, useState } from 'react';
import { MONO } from '@/lib/colors';

const ACCENT = '#A387FF';

const TONE: Record<string, string> = {
  ok: '#38EF7D',
  degraded: '#F5A524',
  failed: '#FC5457',
  skipped: '#6C6C6C',
  never_ran: '#4A4A4A',
};

const MODEL_TONE: Record<string, string> = {
  'gemini-3.8-flash': '#A387FF',
  'gemini-3.1-flash-image': '#38C9EF',
  'nano-banana-pro-preview': '#F5A524',
  'veo-3.1-generate-001': '#FF7AB6',
};

interface GtmAgent {
  n: number;
  id: string;
  name: string;
  role: string;
  model: string | null;
  kind: 'MODEL_BACKED' | 'DETERMINISTIC';
  status: string;
  detail: string;
  outputs: string[];
  at: string | null;
  modelCalls: number;
  modelCallsOk: number;
  inputTokens: number;
  outputTokens: number;
  durationS: number;
}

interface Payload {
  runId: string | null;
  agents: GtmAgent[];
  declared: number;
  modelBacked: number;
  ranThisRun: number;
  failed: string[];
  modelsUsed: string[];
  status: string | null;
}

export function GtmAgents() {
  const [data, setData] = useState<Payload | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch('/api/gtm/agents', { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
      setError(null);
    } catch (e: any) {
      setError(String(e?.message || e));
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 10_000);
    return () => clearInterval(t);
  }, [load]);

  if (error) {
    return (
      <div style={{ color: '#FC5457', fontFamily: MONO, fontSize: 13 }}>
        Could not read agent status: {error}
      </div>
    );
  }
  if (!data) {
    return <div style={{ color: '#6C6C6C', fontFamily: MONO, fontSize: 13 }}>Loading…</div>;
  }

  const noRun = !data.runId;

  return (
    <div>
      <header style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 14, flexWrap: 'wrap' }}>
          <h2 style={{ margin: 0, fontSize: 19, color: '#EDEDED', fontWeight: 600 }}>
            13 GTM Agents
          </h2>
          <span style={{ fontFamily: MONO, fontSize: 12, color: '#6C6C6C' }}>
            {noRun ? 'no run recorded yet' : `${data.runId} · ${data.status}`}
          </span>
        </div>

        <div style={{ display: 'flex', gap: 22, marginTop: 10, flexWrap: 'wrap' }}>
          <Stat label="ran this cycle" value={`${data.ranThisRun}/${data.declared}`} />
          <Stat label="model-backed" value={String(data.modelBacked)} />
          <Stat
            label="failed"
            value={String(data.failed.length)}
            tone={data.failed.length ? '#FC5457' : undefined}
          />
        </div>

        {data.modelsUsed.length > 0 && (
          <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
            {data.modelsUsed.map((m) => (
              <span
                key={m}
                style={{
                  fontFamily: MONO,
                  fontSize: 11,
                  padding: '3px 9px',
                  borderRadius: 4,
                  color: MODEL_TONE[m] || ACCENT,
                  border: `1px solid ${(MODEL_TONE[m] || ACCENT)}44`,
                  background: `${(MODEL_TONE[m] || ACCENT)}11`,
                }}
              >
                {m}
              </span>
            ))}
          </div>
        )}
      </header>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))',
          gap: 12,
        }}
      >
        {data.agents.map((a) => {
          // An agent that should have reasoned but recorded no call is not a
          // healthy agent, even if its stage returned ok.
          const silent = a.kind === 'MODEL_BACKED' && a.status === 'ok' && a.modelCalls === 0;
          const tone = silent ? '#F5A524' : TONE[a.status] || '#4A4A4A';

          return (
            <article
              key={a.id}
              style={{
                border: `1px solid ${tone}33`,
                borderLeft: `2px solid ${tone}`,
                borderRadius: 6,
                padding: '12px 14px',
                background: '#0D0D0F',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                <span style={{ fontFamily: MONO, fontSize: 11, color: '#6C6C6C' }}>
                  A{String(a.n).padStart(2, '0')}
                </span>
                <span style={{ fontFamily: MONO, fontSize: 11, color: tone }}>
                  {silent ? 'ok · no model call' : a.status}
                </span>
              </div>

              <h3 style={{ margin: '6px 0 8px', fontSize: 14, color: '#EDEDED', fontWeight: 600 }}>
                {a.name}
              </h3>

              <div style={{ fontFamily: MONO, fontSize: 11, color: '#8A8A8A', lineHeight: 1.7 }}>
                {a.kind === 'DETERMINISTIC' ? (
                  <div style={{ color: '#6C6C6C' }}>deterministic · no model by design</div>
                ) : (
                  <>
                    <div style={{ color: MODEL_TONE[a.model || ''] || ACCENT }}>{a.model}</div>
                    <div>
                      {a.modelCallsOk}/{a.modelCalls} calls
                      {a.inputTokens > 0 &&
                        ` · ${a.inputTokens.toLocaleString()} in / ${a.outputTokens.toLocaleString()} out`}
                      {a.durationS > 0 && ` · ${a.durationS}s`}
                    </div>
                  </>
                )}
                {a.detail && (
                  <div style={{ color: '#5A5A5A', marginTop: 4 }}>{a.detail.slice(0, 120)}</div>
                )}
              </div>

              {a.outputs.length > 0 && (
                <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {a.id === 'A08_visual_synthesis' && data.runId && (
                    <a
                      href={`/api/gtm/artifact/${data.runId}/visual`}
                      target="_blank"
                      rel="noreferrer"
                      style={linkStyle}
                    >
                      view PNG
                    </a>
                  )}
                  {a.id === 'A09_video_production' && data.runId && (
                    <a
                      href={`/api/gtm/artifact/${data.runId}/video`}
                      target="_blank"
                      rel="noreferrer"
                      style={linkStyle}
                    >
                      play MP4
                    </a>
                  )}
                </div>
              )}
            </article>
          );
        })}
      </div>
    </div>
  );
}

const linkStyle: React.CSSProperties = {
  fontFamily: MONO,
  fontSize: 11,
  color: ACCENT,
  textDecoration: 'none',
  border: `1px solid ${ACCENT}44`,
  borderRadius: 4,
  padding: '2px 8px',
};

function Stat({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div>
      <div style={{ fontFamily: MONO, fontSize: 18, color: tone || '#EDEDED' }}>{value}</div>
      <div style={{ fontFamily: MONO, fontSize: 10, color: '#6C6C6C', textTransform: 'uppercase' }}>
        {label}
      </div>
    </div>
  );
}
