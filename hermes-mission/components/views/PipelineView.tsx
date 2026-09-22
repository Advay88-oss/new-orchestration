'use client';

/**
 * 13-Stage Matrix — the pipeline's own account of itself.
 *
 * Everything here comes from the append-only run journal and the declared
 * routing table. Nothing is synthesised: the old /api/agents/status returned
 * 133 lines of hardcoded JSON with all thirteen agents permanently "connected",
 * in a file that imported `fs` and never used it.
 *
 * The number that matters is "agents that called a model". A stage declared
 * AGENT which recorded no model call is shown in red, because that is exactly
 * the condition the audit found in ten of thirteen stages.
 */

import React, { useCallback, useEffect, useState } from 'react';
import { MONO } from '@/lib/colors';

type Kind = 'AGENT' | 'STAGE';

interface StageView {
  stage: string;
  kind: Kind | null;
  purpose: string;
  state: string;
  status: string | null;
  durationS: number | null;
  model: string | null;
  promptVersion: string | null;
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
  costKnown: boolean;
  attempts: number;
  toolCalls: string[];
  degradedReason: string | null;
  error: string | null;
  agentDidCallModel: boolean | null;
}

interface RunView {
  runId: string;
  directive: string;
  status: string;
  durationS: number | null;
  stages: StageView[];
  costUsd: number;
  costComplete: boolean;
  unpricedModels: string[];
  inputTokens: number;
  outputTokens: number;
  modelCalls: number;
  agentsDeclared: number;
  agentsThatCalledModel: number;
  artifacts: { name: string; path: string; bytes: number }[];
}

interface Route {
  role: string;
  model: string;
  preferred_transport: string;
  effective_transport: string;
  served_by_key: boolean | null;
  degraded: string | null;
  note: string;
}

const ACCENT = '#A387FF';
const TONE: Record<string, string> = {
  succeeded: '#22D3C4',
  degraded: '#F5A524',
  failed: '#FC5457',
  running: '#A387FF',
  not_reached: '#3A3A3A',
};


function Dot({ state }: { state: string }) {
  return (
    <span style={{
      width: 7, height: 7, borderRadius: 999, flex: '0 0 7px',
      background: TONE[state] ?? '#3A3A3A', display: 'inline-block',
    }} />
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="vanna-card" style={{ minWidth: 132, padding: '10px 13px'  }}>
      <div style={{ fontSize: 9, letterSpacing: '.1em', color: '#6A6A6A', textTransform: 'uppercase' }}>
        {label}
      </div>
      <div style={{ fontSize: 15, fontWeight: 600, marginTop: 3, color: tone ?? '#EDEDED', fontFamily: MONO }}>
        {value}
      </div>
    </div>
  );
}

export function PipelineView() {
  const [runs, setRuns] = useState<RunView[]>([]);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [vertex, setVertex] = useState<{ available: boolean; reason: string } | null>(null);
  const [sel, setSel] = useState<string | null>(null);
  const [worker, setWorker] = useState<any>(null);
  const [directive, setDirective] = useState('');
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [rr, mm, hh] = await Promise.all([
        fetch('/api/v2/runs?limit=20', { cache: 'no-store' }),
        fetch('/api/v2/manifest', { cache: 'no-store' }),
        fetch('/api/v2/health', { cache: 'no-store' }),
      ]);
      if (!rr.ok) throw new Error(`runs HTTP ${rr.status}`);
      const rj = await rr.json();
      const mj = mm.ok ? await mm.json() : {};
      const hj = hh.ok ? await hh.json() : {};
      setRuns(rj.runs ?? []);
      setRoutes(mj.routing ?? []);
      setVertex(mj.vertex ?? null);
      setWorker(hj.worker ?? null);
      setSel((c) => c ?? rj.runs?.[0]?.runId ?? null);
      setErr(null);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [load]);

  const run = runs.find((r) => r.runId === sel) ?? null;

  async function queue() {
    const res = await fetch('/api/v2/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ directive }),
    });
    const j = await res.json();
    setMsg(j.note ?? 'queued');
    setDirective('');
    load();
  }

  return (
    <div className="vanna-section" style={{ padding: 0 }}>
      <div>
        <h2 style={{ fontSize: 17, fontWeight: 700, margin: 0, color: '#EDEDED' }}>13-Stage Matrix</h2>
        <p style={{ fontSize: 12, color: '#7A7A7A', marginTop: 5, maxWidth: 720, lineHeight: 1.5 }}>
          Read from the append-only run journal. A stage counts as an agent only if the manifest
          declares it one, and counts as having reasoned only if it recorded a real model call.
        </p>
      </div>

      {err && (
        <div className="vanna-card" style={{ borderColor: '#5E0D46', color: '#FC5457', fontSize: 12.5  }}>
          Backend unreachable: {err}. Nothing is shown from cache — this view has no fixtures.
        </div>
      )}

      {/* ---------- model routing ---------- */}
      <div className="vanna-card">
        <div style={{ fontSize: 10, letterSpacing: '.1em', color: '#6A6A6A', textTransform: 'uppercase' }}>
          Model routing
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(250px,1fr))', gap: 10, marginTop: 11 }}>
          {routes.map((r) => (
            <div key={r.role} style={{ border: '1px solid #1C1C1C', borderRadius: 8, padding: '9px 11px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: ACCENT, textTransform: 'uppercase', letterSpacing: '.07em' }}>
                  {r.role}
                </span>
                <span style={{
                  marginLeft: 'auto', fontSize: 9.5, padding: '1px 6px', borderRadius: 4,
                  background: r.effective_transport === 'vertex' ? '#13303A' : '#241C3A',
                  color: r.effective_transport === 'vertex' ? '#22D3C4' : '#A387FF',
                }}>
                  {r.effective_transport}
                </span>
              </div>
              <div style={{ fontFamily: MONO, fontSize: 12, marginTop: 4, color: '#EDEDED' }}>{r.model}</div>
              <div style={{ fontSize: 10.5, color: '#6A6A6A', marginTop: 3 }}>{r.note}</div>
              {r.served_by_key === false && (
                <div style={{ fontSize: 10.5, color: '#FC5457', marginTop: 4 }}>not served by this key</div>
              )}
              {r.degraded && (
                <div style={{ fontSize: 10.5, color: '#F5A524', marginTop: 4 }}>
                  {r.preferred_transport} → {r.effective_transport}: {r.degraded}
                </div>
              )}
            </div>
          ))}
        </div>
        {vertex && !vertex.available && (
          <div style={{ fontSize: 11, color: '#F5A524', marginTop: 11 }}>
            Vertex is not reachable, so roles that prefer it are being served over the API key.
            The model is unchanged; only the transport differs. Restore with{' '}
            <code style={{ fontFamily: MONO }}>gcloud auth application-default login</code>.
          </div>
        )}
      </div>

      {/* ---------- trigger ---------- */}
      <div style={{ display: 'flex', gap: 8 }}>
        <input
          value={directive}
          onChange={(e) => setDirective(e.target.value)}
          placeholder="Directive… (say 'video' for Veo, 'meme' for nano banana pro)"
          style={{
            flex: 1, padding: '10px 12px', borderRadius: 8, border: '1px solid #232323',
            background: '#0D0D0D', color: '#EDEDED', fontSize: 12.5,
          }}
        />
        <button
          onClick={queue}
          style={{
            padding: '10px 20px', borderRadius: 8, border: 'none', cursor: 'pointer',
            background: ACCENT, color: '#07020D', fontWeight: 700, fontSize: 12.5,
          }}
        >
          Queue run
        </button>
      </div>
      {msg && (
        <p style={{ fontSize: 11.5, color: worker?.alive ? '#7A7A7A' : '#F5A524', margin: 0 }}>{msg}</p>
      )}
      {worker && !worker.alive && (
        <p style={{ fontSize: 11.5, color: '#FC5457', margin: 0 }}>
          No worker is running — queued jobs will sit until one starts:{' '}
          <code style={{ fontFamily: MONO }}>python -m core.worker</code>
        </p>
      )}

      {/* ---------- runs ---------- */}
      <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}>
        {runs.map((r) => (
          <button
            key={r.runId}
            onClick={() => setSel(r.runId)}
            style={{
              padding: '6px 10px', borderRadius: 7, fontSize: 11.5, cursor: 'pointer',
              border: `1px solid ${r.runId === sel ? ACCENT : '#232323'}`,
              background: r.runId === sel ? '#17132A' : '#0D0D0D',
              color: '#EDEDED', display: 'flex', alignItems: 'center', gap: 6, fontFamily: MONO,
            }}
          >
            <Dot state={r.status === 'ok' ? 'succeeded' : r.status} />
            {r.runId.replace('RUN-', '')}
          </button>
        ))}
        {runs.length === 0 && !err && (
          <p style={{ fontSize: 12.5, color: '#7A7A7A', margin: 0 }}>No runs yet — queue one above.</p>
        )}
      </div>

      {run && (
        <>
          <div style={{ display: 'flex', gap: 9, flexWrap: 'wrap' }}>
            <Stat label="status" value={run.status}
                  tone={run.status === 'ok' ? '#22D3C4' : run.status === 'degraded' ? '#F5A524' : '#FC5457'} />
            <Stat
              label="agents that reasoned"
              value={`${run.agentsThatCalledModel} / ${run.agentsDeclared}`}
              tone={run.agentsThatCalledModel === run.agentsDeclared ? '#22D3C4' : '#F5A524'}
            />
            <Stat label="model calls" value={String(run.modelCalls)} />
            <Stat label="tokens" value={`${run.inputTokens}/${run.outputTokens}`} />
            <Stat label="cost"
                  value={run.costComplete ? `$${run.costUsd.toFixed(4)}` : `$${run.costUsd.toFixed(4)}+`}
                  tone={run.costComplete ? undefined : '#F5A524'} />
            <Stat label="duration" value={run.durationS ? `${run.durationS}s` : '—'} />
          </div>

          {!run.costComplete && (
            <p style={{ fontSize: 11.5, color: '#F5A524', margin: 0 }}>
              No published rate held for {run.unpricedModels.join(', ')} — the figure above is
              incomplete, not zero.
            </p>
          )}

          <div className="vanna-card" style={{ padding: 0, overflowX: 'auto'  }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ color: '#6A6A6A', textAlign: 'left' }}>
                  {['#', 'stage', 'kind', 'state', 'model', 'prompt', 'tokens', 'tools', 'time'].map((h) => (
                    <th key={h} style={{ padding: '9px 11px', fontWeight: 500, fontSize: 10, letterSpacing: '.07em', textTransform: 'uppercase' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {run.stages.map((s, i) => (
                  <tr key={s.stage} style={{ borderTop: '1px solid #1A1A1A' }}>
                    <td style={{ padding: '10px 11px', color: '#4A4A4A', fontFamily: MONO }}>{i + 1}</td>
                    <td style={{ padding: '10px 11px' }}>
                      <div style={{ fontWeight: 600, color: '#EDEDED' }}>{s.stage}</div>
                      <div style={{ color: '#6A6A6A', fontSize: 11, marginTop: 2 }}>{s.purpose}</div>
                      {s.degradedReason && (
                        <div style={{ color: '#F5A524', fontSize: 11, marginTop: 4, maxWidth: 460 }}>
                          {s.degradedReason}
                        </div>
                      )}
                      {s.error && (
                        <div style={{ color: '#FC5457', fontSize: 11, marginTop: 4, maxWidth: 460 }}>{s.error}</div>
                      )}
                    </td>
                    <td style={{ padding: '10px 11px' }}>
                      <span style={{
                        fontSize: 10, padding: '2px 6px', borderRadius: 4, letterSpacing: '.05em',
                        background: s.kind === 'AGENT' ? '#241C3A' : '#1A1A1A',
                        color: s.kind === 'AGENT' ? '#A387FF' : '#7A7A7A',
                      }}>
                        {s.kind}
                      </span>
                      {s.agentDidCallModel === false && (
                        <div style={{ color: '#FC5457', fontSize: 10, marginTop: 4 }}>no model call</div>
                      )}
                    </td>
                    <td style={{ padding: '10px 11px' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#EDEDED' }}>
                        <Dot state={s.state} />{s.state}
                      </span>
                    </td>
                    <td style={{ padding: '10px 11px', fontFamily: MONO, fontSize: 11 }}>{s.model ?? '—'}</td>
                    <td style={{ padding: '10px 11px', fontFamily: MONO, fontSize: 10.5, color: '#7A7A7A' }}>
                      {s.promptVersion ?? '—'}
                    </td>
                    <td style={{ padding: '10px 11px', fontFamily: MONO, fontSize: 11 }}>
                      {s.inputTokens || s.outputTokens ? `${s.inputTokens}/${s.outputTokens}` : '—'}
                    </td>
                    <td style={{ padding: '10px 11px', fontSize: 10.5, color: '#6A6A6A' }}>
                      {s.toolCalls?.length ? s.toolCalls.join(', ') : '—'}
                    </td>
                    <td style={{ padding: '10px 11px', color: '#7A7A7A', fontFamily: MONO, fontSize: 11 }}>
                      {s.durationS != null ? `${s.durationS}s` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {run.artifacts.filter((a) => a.name.endsWith('.png')).length > 0 && (
            <div>
              <div style={{ fontSize: 10, letterSpacing: '.1em', color: '#6A6A6A', textTransform: 'uppercase' }}>
                Artifacts
              </div>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 10 }}>
                {run.artifacts
                  .filter((a) => a.name.endsWith('.png'))
                  .slice(-3)
                  .map((a) => (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      key={a.path}
                      src={`/api/v2/artifact/${run.runId}?path=${encodeURIComponent(a.path)}`}
                      alt={a.name}
                      style={{ width: 240, borderRadius: 10, border: '1px solid #232323' }}
                    />
                  ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
